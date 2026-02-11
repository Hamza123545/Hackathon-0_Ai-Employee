'use client';

import { motion } from 'framer-motion';
import React from 'react';
import { Card } from './card';

export default function AnimatedCard({ children, className, delay = 0 }: { children: React.ReactNode, className?: string, delay?: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay, ease: 'easeOut' }}
            whileHover={{ y: -5, transition: { duration: 0.2 } }}
            className={className}
        >
            <Card className="h-full">
                {children}
            </Card>
        </motion.div>
    );
}
