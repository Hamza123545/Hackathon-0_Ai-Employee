import React from 'react';
import Dashboard from '@/components/Dashboard';
import PageTransition from '@/components/ui/PageTransition';

export default function Home() {
  return (
    <PageTransition className="p-8 space-y-8">
      <header className="flex justify-between items-center border-b pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of system status and approvals</p>
        </div>
      </header>

      <Dashboard />
    </PageTransition>
  );
}
