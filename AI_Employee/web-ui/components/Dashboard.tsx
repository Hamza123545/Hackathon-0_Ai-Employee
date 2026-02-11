'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AnimatedCard from "@/components/ui/AnimatedCard";
import { Activity, CheckCircle, Clock, AlertCircle } from "lucide-react";

export default function Dashboard() {
    const [stats, setStats] = useState({
        pending: 0,
        tasks: 0,
        completed: 0,
    });

    useEffect(() => {
        // Poll for stats
        const fetchStats = async () => {
            try {
                const [tasksRes, approvalsRes] = await Promise.all([
                    fetch('/api/tasks'),
                    fetch('/api/approvals')
                ]);

                const tasksData = await tasksRes.json();
                const approvalsData = await approvalsRes.json();

                setStats({
                    pending: approvalsData.approvals?.length || 0,
                    tasks: tasksData.tasks?.length || 0,
                    completed: 0 // Placeholder for now
                });
            } catch (error) {
                console.error("Failed to fetch stats", error);
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 5000); // Live update
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
                <AnimatedCard delay={0.1}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.pending}</div>
                        <p className="text-xs text-muted-foreground">Requires human attention</p>
                    </CardContent>
                </AnimatedCard>

                <AnimatedCard delay={0.2}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
                        <Clock className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.tasks}</div>
                        <p className="text-xs text-muted-foreground">In /Needs_Action queue</p>
                    </CardContent>
                </AnimatedCard>

                <AnimatedCard delay={0.3}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
                        <CheckCircle className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.completed}</div>
                        <p className="text-xs text-muted-foreground">Items in /Done</p>
                    </CardContent>
                </AnimatedCard>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <AnimatedCard delay={0.4} className="col-span-4">
                    <CardHeader>
                        <CardTitle>Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {/* Mock activity feed */}
                            <div className="flex items-center">
                                <Activity className="mr-2 h-4 w-4 opacity-70" />
                                <span className="text-sm">Agent started watching /Needs_Action</span>
                                <span className="ml-auto text-xs text-muted-foreground">Just now</span>
                            </div>
                        </div>
                    </CardContent>
                </AnimatedCard>
            </div>
        </div>
    );
}
