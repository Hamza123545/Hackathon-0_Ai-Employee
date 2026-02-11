'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Square, RefreshCw, Cpu, Database } from "lucide-react";
import { motion, AnimatePresence } from 'framer-motion';

interface Process {
    name: string;
    id: number;
    status: 'online' | 'stopped' | 'errored' | 'launching';
    memory: number;
    cpu: number;
}

export default function ServiceManager() {
    const [processes, setProcesses] = useState<Process[]>([]);
    const [loading, setLoading] = useState<string | null>(null);

    const fetchProcesses = async () => {
        try {
            const res = await fetch('/api/processes');
            if (res.ok) {
                const data = await res.json();
                setProcesses(data.processes || []);
            }
        } catch (error) {
            console.error("Failed to fetch processes");
        }
    };

    useEffect(() => {
        fetchProcesses();
        const interval = setInterval(fetchProcesses, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleAction = async (name: string, action: string) => {
        setLoading(name);
        try {
            await fetch('/api/processes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, action }),
            });
            // specific small delay to let PM2 react
            setTimeout(fetchProcesses, 1000);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(null);
        }
    };

    const formatMemory = (bytes: number) => {
        return Math.round(bytes / 1024 / 1024) + ' MB';
    };

    if (processes.length === 0) {
        return (
            <Card className="border-dashed">
                <CardHeader><CardTitle>Service Manager</CardTitle></CardHeader>
                <CardContent className="text-muted-foreground text-sm">
                    No PM2 processes detected. Is PM2 running?
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
                {processes.map((proc) => (
                    <motion.div
                        key={proc.id}
                        layout
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        transition={{ duration: 0.2 }}
                    >
                        <Card className="relative overflow-hidden h-full">
                            {/* Status Bar */}
                            <div className={`absolute top-0 left-0 w-1 h-full ${proc.status === 'online' ? 'bg-green-500' :
                                    proc.status === 'stopped' ? 'bg-gray-400' : 'bg-red-500'
                                }`} />

                            <CardHeader className="pb-2">
                                <div className="flex justify-between items-start">
                                    <CardTitle className="text-base font-semibold">{proc.name}</CardTitle>
                                    <div className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${proc.status === 'online' ? 'bg-green-100 text-green-700' :
                                            proc.status === 'stopped' ? 'bg-gray-100 text-gray-600' : 'bg-red-100 text-red-700'
                                        }`}>
                                        {proc.status}
                                        {proc.status === 'online' && (
                                            <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                        )}
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="flex space-x-4 text-xs text-muted-foreground mb-4">
                                    <div className="flex items-center"><Database className="mr-1 h-3 w-3" /> {formatMemory(proc.memory)}</div>
                                    <div className="flex items-center"><Cpu className="mr-1 h-3 w-3" /> {proc.cpu}%</div>
                                </div>

                                <div className="flex space-x-2">
                                    {proc.status !== 'online' ? (
                                        <Button
                                            size="sm" variant="default" className="w-full bg-green-600 hover:bg-green-700 text-white"
                                            onClick={() => handleAction(proc.name, 'start')}
                                            disabled={loading === proc.name}
                                        >
                                            <Play className="mr-2 h-3 w-3" /> Start
                                        </Button>
                                    ) : (
                                        <Button
                                            size="sm" variant="destructive" className="w-full"
                                            onClick={() => handleAction(proc.name, 'stop')}
                                            disabled={loading === proc.name}
                                        >
                                            <Square className="mr-2 h-3 w-3" /> Stop
                                        </Button>
                                    )}
                                    <Button
                                        size="sm" variant="outline" className="w-full"
                                        onClick={() => handleAction(proc.name, 'restart')}
                                        disabled={loading === proc.name}
                                    >
                                        <RefreshCw className={`mr-2 h-3 w-3 ${loading === proc.name ? 'animate-spin' : ''}`} /> Restart
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                ))}
            </AnimatePresence>
        </div>
    );
}
