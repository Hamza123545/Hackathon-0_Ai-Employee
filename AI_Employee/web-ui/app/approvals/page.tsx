'use client';

import React from 'react';
import ApprovalWorkflow from '@/components/ApprovalWorkflow';
import PageTransition from '@/components/ui/PageTransition';

export default function ApprovalsPage() {
    return (
        <PageTransition className="p-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Approvals</h1>
                <p className="text-muted-foreground">Review and authorize pending actions.</p>
            </div>

            <div className="max-w-4xl">
                <ApprovalWorkflow />
            </div>
        </PageTransition>
    );
}
