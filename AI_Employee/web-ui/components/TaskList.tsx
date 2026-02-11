'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Clock } from "lucide-react";

interface Task {
    id: string;
    name: string;
    created: string;
    content: string;
}

export default function TaskList() {
    const [tasks, setTasks] = useState<Task[]>([]);

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const res = await fetch('/api/tasks');
                const data = await res.json();
                setTasks(data.tasks || []);
            } catch (error) {
                console.error("Failed to fetch tasks", error);
            }
        };

        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, []);

    if (tasks.length === 0) {
        return (
            <Card>
                <CardHeader><CardTitle>Active Tasks</CardTitle></CardHeader>
                <CardContent className="text-muted-foreground text-sm">No active tasks in queue.</CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Active Tasks ({tasks.length})</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {tasks.slice(0, 5).map((task) => ( // Show top 5
                        <div key={task.id} className="flex items-start space-x-3 p-3 rounded-md border bg-muted/50">
                            <FileText className="h-5 w-5 mt-0.5 text-blue-500" />
                            <div className="space-y-1">
                                <p className="text-sm font-medium leading-none">{task.name}</p>
                                <p className="text-xs text-muted-foreground line-clamp-2">{task.content}</p>
                                <div className="flex items-center text-xs text-muted-foreground pt-1">
                                    <Clock className="mr-1 h-3 w-3" />
                                    {new Date(task.created).toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
