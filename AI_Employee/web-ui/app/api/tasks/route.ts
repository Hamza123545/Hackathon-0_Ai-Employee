import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Configuration
// In a real deployment, this would come from process.env.VAULT_ROOT
// For local dev, we assume the specific path
const VAULT_ROOT = process.env.VAULT_ROOT || 'd:\\Hackathon-0_Ai-Employee\\AI_Employee';
const NEEDS_ACTION_DIR = path.join(VAULT_ROOT, 'Needs_Action');

export async function GET() {
    try {
        // Ensure directory exists
        if (!fs.existsSync(NEEDS_ACTION_DIR)) {
            return NextResponse.json({ tasks: [], message: 'Directory not found' });
        }

        const files = await fs.promises.readdir(NEEDS_ACTION_DIR);

        // Filter for markdown files and get stats
        const tasks = await Promise.all(
            files
                .filter(file => file.endsWith('.md') || file.endsWith('.txt'))
                .map(async (file) => {
                    const filePath = path.join(NEEDS_ACTION_DIR, file);
                    const stats = await fs.promises.stat(filePath);
                    const content = await fs.promises.readFile(filePath, 'utf-8');

                    return {
                        id: file,
                        name: file,
                        created: stats.birthtime,
                        content: content.slice(0, 200) + (content.length > 200 ? '...' : ''), // Preview
                        path: filePath
                    };
                })
        );

        // Sort by newest first
        tasks.sort((a, b) => b.created.getTime() - a.created.getTime());

        return NextResponse.json({ tasks });
    } catch (error) {
        console.error('Error reading tasks:', error);
        return NextResponse.json(
            { error: 'Failed to fetch tasks' },
            { status: 500 }
        );
    }
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { title, content } = body;

        if (!title || !content) {
            return NextResponse.json(
                { error: 'Title and content are required' },
                { status: 400 }
            );
        }

        const safeTitle = title.replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const fileName = `${safeTitle}_${Date.now()}.md`;
        const filePath = path.join(NEEDS_ACTION_DIR, fileName);

        await fs.promises.writeFile(filePath, content, 'utf-8');

        return NextResponse.json({ success: true, fileName });
    } catch (error) {
        console.error('Error creating task:', error);
        return NextResponse.json(
            { error: 'Failed to create task' },
            { status: 500 }
        );
    }
}
