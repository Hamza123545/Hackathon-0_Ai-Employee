'use client';

import React from 'react';
import TaskCreator from '@/components/TaskCreator';
import TaskList from '@/components/TaskList';
import PageTransition from '@/components/ui/PageTransition';

export default function TasksPage() {
    return (
        <PageTransition className="p-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
                <p className="text-muted-foreground">Manage and assign new tasks to your AI Employee.</p>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">Create New Task</h2>
                    <TaskCreator />
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">Active Queue</h2>
                    <TaskList />
                </section>
            </div>
        </PageTransition>
    );
}
