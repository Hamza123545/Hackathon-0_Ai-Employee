'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X } from "lucide-react";

interface Approval {
    id: string;
    name: string;
    content: string;
    created: string;
}

export default function ApprovalWorkflow() {
    const [approvals, setApprovals] = useState<Approval[]>([]);

    const fetchApprovals = async () => {
        const res = await fetch('/api/approvals');
        const data = await res.json();
        setApprovals(data.approvals || []);
    };

    useEffect(() => {
        fetchApprovals();
    }, []);

    const handleAction = async (id: string, action: 'approve' | 'reject') => {
        try {
            await fetch('/api/approvals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, action }),
            });
            // Refresh list
            fetchApprovals();
        } catch (error) {
            console.error("Action failed", error);
        }
    };

    if (approvals.length === 0) {
        return <div className="p-4 text-center text-muted-foreground">No pending approvals. Good job!</div>;
    }

    return (
        <div className="grid gap-4 md:grid-cols-2">
            {approvals.map((approval) => (
                <Card key={approval.id}>
                    <CardHeader>
                        <CardTitle className="text-lg">{approval.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <pre className="p-4 bg-muted rounded-md text-sm overflow-auto max-h-48 whitespace-pre-wrap">
                            {approval.content}
                        </pre>
                    </CardContent>
                    <CardFooter className="flex justify-end space-x-2">
                        <Button variant="destructive" size="sm" onClick={() => handleAction(approval.id, 'reject')}>
                            <X className="mr-2 h-4 w-4" /> Reject
                        </Button>
                        <Button variant="default" size="sm" onClick={() => handleAction(approval.id, 'approve')}>
                            <Check className="mr-2 h-4 w-4" /> Approve
                        </Button>
                    </CardFooter>
                </Card>
            ))}
        </div>
    );
}
