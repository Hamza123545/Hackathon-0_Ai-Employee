'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export default function TaskCreator() {
    const [content, setContent] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!content.trim()) return;

        setIsSubmitting(true);
        try {
            const title = content.split('\n')[0].substring(0, 30) || 'New Task';

            const res = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content }),
            });

            if (res.ok) {
                setContent('');
                // Ideally trigger a refresh in parent/context, but for now simple clear
                alert('Task created successfully!');
                window.location.reload(); // Simple refresh to show new stats
            } else {
                alert('Failed to create task');
            }
        } catch (error) {
            console.error(error);
            alert('Error creating task');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Create New Task</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <textarea
                        className="w-full min-h-[100px] p-3 rounded-md border text-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
                        placeholder="Describe the task for your AI Employee..."
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        disabled={isSubmitting}
                    />
                </form>
            </CardContent>
            <CardFooter className="flex justify-end">
                <Button onClick={handleSubmit} disabled={isSubmitting || !content.trim()}>
                    <Send className="mr-2 h-4 w-4" />
                    {isSubmitting ? 'Sending...' : 'Assign Task'}
                </Button>
            </CardFooter>
        </Card>
    );
}
