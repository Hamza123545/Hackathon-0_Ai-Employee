import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';

const execPromise = util.promisify(exec);

// Helper to execute PM2 commands
async function runPm2(command: string) {
    try {
        // Note: This relies on 'pm2' being in the PATH of the server process
        const { stdout, stderr } = await execPromise(`pm2 ${command}`);
        if (stderr && stderr.length > 0) {
            // PM2 often writes non-errors to stderr, so we log but don't fail immediately
            console.warn('PM2 Stderr:', stderr);
        }
        return JSON.parse(stdout);
    } catch (error) {
        console.error(`PM2 Error (${command}):`, error);
        throw error;
    }
}

export async function GET() {
    try {
        // Get list in JSON format
        const processes = await runPm2('jlist');

        // Map to cleaner format
        const cleanList = processes.map((proc: any) => ({
            name: proc.name,
            id: proc.pm_id,
            status: proc.pm2_env.status, // 'online', 'stopped', 'errored'
            uptime: proc.pm2_env.pm_uptime,
            memory: proc.monit?.memory || 0,
            cpu: proc.monit?.cpu || 0
        }));

        return NextResponse.json({ processes: cleanList });
    } catch (error) {
        return NextResponse.json(
            { error: 'Failed to fetch process list. Is PM2 running?' },
            { status: 500 }
        );
    }
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { name, action } = body;

        if (!name || !action) {
            return NextResponse.json(
                { error: 'Process name and action are required' },
                { status: 400 }
            );
        }

        // Validate action to prevent injection
        const allowedActions = ['start', 'stop', 'restart', 'delete'];
        if (!allowedActions.includes(action)) {
            return NextResponse.json(
                { error: 'Invalid action' },
                { status: 400 }
            );
        }

        // Execute command (e.g., 'pm2 stop gmail-watcher')
        // We use plain exec here because some return text, not JSON
        await execPromise(`pm2 ${action} ${name}`);

        return NextResponse.json({ success: true, name, action });
    } catch (error) {
        return NextResponse.json(
            { error: `Failed to ${action} process` },
            { status: 500 }
        );
    }
}
