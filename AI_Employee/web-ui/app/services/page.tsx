'use client';

import React from 'react';
import ServiceManager from '@/components/ServiceManager';
import PageTransition from '@/components/ui/PageTransition';

export default function ServicesPage() {
    return (
        <PageTransition className="p-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Services</h1>
                <p className="text-muted-foreground">Monitor and control background watchers and agents.</p>
            </div>

            <ServiceManager />
        </PageTransition>
    );
}
