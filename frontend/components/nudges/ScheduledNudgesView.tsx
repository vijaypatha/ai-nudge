// frontend/components/nudges/ScheduledNudgesView.tsx
// --- NEW COMPONENT ---

'use client';

import { FC } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Client, ScheduledMessage } from '@/context/AppContext';
import { Avatar } from '@/components/ui/Avatar';
import { CalendarClock, CalendarPlus, ChevronRight, Loader2 } from 'lucide-react';

interface ScheduledNudgesViewProps {
    messages: ScheduledMessage[];
    isLoading: boolean;
    clients: Client[];
}

export const ScheduledNudgesView: FC<ScheduledNudgesViewProps> = ({ messages, isLoading, clients }) => {
    const router = useRouter();
    const findClientName = (clientId: string) => clients.find(c => c.id === clientId)?.full_name || 'Unknown Client';

    if (isLoading) {
        return <div className="text-center py-20 text-brand-text-muted"><Loader2 className="mx-auto h-12 w-12 animate-spin"/></div>;
    }

    if (messages.length === 0) {
        return (
            <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
                <CalendarClock className="mx-auto h-16 w-16 text-brand-text-muted" />
                <h3 className="mt-4 text-xl font-medium text-brand-white">Nothing Scheduled</h3>
                <p className="mt-1 text-base text-brand-text-muted">Approve an AI-Suggested Plan to see your scheduled messages here.</p>
            </div>
        );
    }

    return (
        <motion.div 
            variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.05 } } }} 
            initial="hidden" 
            animate="visible" 
            className="space-y-4 max-w-4xl mx-auto"
        >
             {messages.map(msg => (
                <motion.div 
                    key={msg.id} 
                    variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }} 
                    className="bg-brand-primary border border-white/10 rounded-xl p-4 flex items-start gap-4 hover:bg-white/5 transition-colors cursor-pointer"
                    onClick={() => router.push(`/conversations/${msg.client_id}`)}
                >
                    <Avatar name={findClientName(msg.client_id)} className="w-10 h-10 mt-1 flex-shrink-0" />
                    <div className="flex-grow">
                        <div className="flex justify-between items-center">
                            <p className="font-bold text-brand-text-main">{findClientName(msg.client_id)}</p>
                            <p className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                                <CalendarPlus size={16}/>
                                Scheduled for: {new Date(msg.scheduled_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}
                            </p>
                        </div>
                        <p className="text-brand-text-muted mt-2 italic">"{msg.content}"</p>
                    </div>
                    <ChevronRight className="flex-shrink-0 text-brand-text-muted self-center"/>
                </motion.div>
             ))}
        </motion.div>
    );
};
