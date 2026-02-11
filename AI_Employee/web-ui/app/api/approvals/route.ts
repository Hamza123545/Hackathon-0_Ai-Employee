import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const VAULT_ROOT = process.env.VAULT_ROOT || 'd:\\Hackathon-0_Ai-Employee\\AI_Employee';
const PENDING_DIR = path.join(VAULT_ROOT, 'Pending_Approval');
const APPROVED_DIR = path.join(VAULT_ROOT, 'Approved');
const REJECTED_DIR = path.join(VAULT_ROOT, 'Rejected');

export async function GET() {
    try {
        if (!fs.existsSync(PENDING_DIR)) {
            return NextResponse.json({ approvals: [] });
        }

        const files = await fs.promises.readdir(PENDING_DIR);

        // Filter for JSON/YAML/TXT files
        const approvals = await Promise.all(
            files.map(async (file) => {
                const filePath = path.join(PENDING_DIR, file);
                const stats = await fs.promises.stat(filePath);
                const content = await fs.promises.readFile(filePath, 'utf-8');

                return {
                    id: file,
                    name: file,
                    created: stats.birthtime,
                    content: content,
                    path: filePath
                };
            })
        );

        // Sort by oldest first (FIFO)
        approvals.sort((a, b) => a.created.getTime() - b.created.getTime());

        return NextResponse.json({ approvals });
    } catch (error) {
        console.error('Error reading approvals:', error);
        return NextResponse.json(
            { error: 'Failed to fetch approvals' },
            { status: 500 }
        );
    }
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { id, action } = body; // action: 'approve' | 'reject'

        if (!id || !action) {
            return NextResponse.json(
                { error: 'ID and action are required' },
                { status: 400 }
            );
        }

        const sourcePath = path.join(PENDING_DIR, id);

        if (!fs.existsSync(sourcePath)) {
            return NextResponse.json(
                { error: 'Approval request not found' },
                { status: 404 }
            );
        }

        let targetDir;
        if (action === 'approve') {
            targetDir = APPROVED_DIR;
        } else if (action === 'reject') {
            targetDir = REJECTED_DIR;
        } else {
            return NextResponse.json(
                { error: 'Invalid action' },
                { status: 400 }
            );
        }

        // Ensure target dir exists
        if (!fs.existsSync(targetDir)) {
            await fs.promises.mkdir(targetDir, { recursive: true });
        }

        const targetPath = path.join(targetDir, id);

        // Move file
        await fs.promises.rename(sourcePath, targetPath);

        return NextResponse.json({ success: true, action, id });

    } catch (error) {
        console.error('Error processing approval:', error);
        return NextResponse.json(
            { error: 'Failed to process approval' },
            { status: 500 }
        );
    }
}
