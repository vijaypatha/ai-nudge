// frontend/components/nudges/ScheduledNudgesView.tsx
// --- DEFINITIVE FIX: Corrects timezone conversion logic for grouping and display.

'use client';

import { FC, useMemo, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Client, ScheduledMessage, useAppContext, User } from '@/context/AppContext';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { EditMessageModal } from '@/components/modals/EditMessageModal';
import { CalendarClock, CalendarPlus, ChevronRight, Loader2, Edit, Trash2 } from 'lucide-react';

interface ScheduledNudgesViewProps {
    messages: ScheduledMessage[];
    isLoading: boolean;
    clients: Client[];
    user: User | null;
    onAction: () => void;
}

const groupMessagesByDate = (messages: ScheduledMessage[], localTimeZone: string) => {
    const groups: { [key: string]: ScheduledMessage[] } = { Today: [], Tomorrow: [], 'This Week': [], 'Later': [] };
    const dateFormatter = new Intl.DateTimeFormat('en-CA', { timeZone: localTimeZone, year: 'numeric', month: '2-digit', day: '2-digit' });
    const todayStr = dateFormatter.format(new Date());

    messages.forEach(msg => {
        // FIX: Ensure the date string from the backend is explicitly parsed as UTC
        const utcDateString = msg.scheduled_at.endsWith('Z') ? msg.scheduled_at : `${msg.scheduled_at}Z`;
        const msgDate = new Date(utcDateString);

        const msgDateStr = dateFormatter.format(msgDate);
        const diffDays = Math.round((new Date(msgDateStr).getTime() - new Date(todayStr).getTime()) / 86400000);

        if (diffDays < 0) groups.Later.push(msg); // Should not happen with pending filter
        else if (diffDays === 0) groups.Today.push(msg);
        else if (diffDays === 1) groups.Tomorrow.push(msg);
        else if (diffDays > 1 && diffDays <= 7) groups['This Week'].push(msg);
        else groups.Later.push(msg);
    });
    return groups;
};

const formatDateTimezone = (dateString: string, timeZone: string) => {
    // FIX: Ensure the date string from the backend is explicitly parsed as UTC.
    // The 'Z' suffix tells the JavaScript Date object that the time is UTC.
    const utcDateString = dateString.endsWith('Z') ? dateString : `${dateString}Z`;

    const options: Intl.DateTimeFormatOptions = {
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        timeZoneName: 'short',
        timeZone: timeZone,
    };
    try {
        return new Intl.DateTimeFormat('en-US', options).format(new Date(utcDateString));
    } catch (e) {
        // Fallback for any unexpected errors
        return new Date(utcDateString).toLocaleString();
    }
};

export const ScheduledNudgesView: FC<ScheduledNudgesViewProps> = ({ messages, isLoading, clients, user, onAction }) => {
    const router = useRouter();
    const { api } = useAppContext();
    const [editingMessage, setEditingMessage] = useState<ScheduledMessage | null>(null);
    const [processingId, setProcessingId] = useState<string | null>(null);

    const userTimezone = user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
    const findClient = (clientId: string) => clients.find(c => c.id === clientId);
    const groupedMessages = useMemo(() => groupMessagesByDate(messages, userTimezone), [messages, userTimezone]);

    const handleCancel = useCallback(async (messageId: string) => {
        if (!window.confirm("Are you sure you want to cancel this scheduled message?")) return;
        setProcessingId(messageId);
        try {
            await api.put(`/api/scheduled-messages/${messageId}`, { status: 'cancelled' });
            onAction();
        } catch (error) {
            console.error("Failed to cancel message:", error);
            alert("Could not cancel the message.");
        } finally {
            setProcessingId(null);
        }
    }, [api, onAction]);

    if (isLoading) return <div className="text-center py-20 text-brand-text-muted"><Loader2 className="mx-auto h-12 w-12 animate-spin"/></div>;
    if (messages.length === 0) return (
        <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
            <CalendarClock className="mx-auto h-16 w-16 text-brand-text-muted" />
            <h3 className="mt-4 text-xl font-medium text-brand-white">Nothing Scheduled</h3>
            <p className="mt-1 text-base text-brand-text-muted">Approve an AI-Suggested Plan to see messages here.</p>
        </div>
    );

    return (
        <>
            <EditMessageModal isOpen={!!editingMessage} onClose={() => setEditingMessage(null)} message={editingMessage} onSaveSuccess={() => { setEditingMessage(null); onAction(); }} />
            <div className="space-y-8 max-w-4xl mx-auto">
                {Object.entries(groupedMessages).map(([groupTitle, groupMessages]) => {
                    if (groupMessages.length === 0) return null;
                    return (
                        <motion.div key={groupTitle} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <h2 className="text-lg font-bold text-white mb-4">{groupTitle} ({groupMessages.length})</h2>
                            <div className="space-y-3">
                                {groupMessages.map(msg => {
                                    const client = findClient(msg.client_id);
                                    const clientName = client?.full_name || 'Unknown Client';
                                    const effectiveTimezone = client?.timezone || userTimezone;
                                    return (
                                        <motion.div key={msg.id} className="bg-brand-primary border border-white/10 rounded-xl p-4">
                                            <div className="flex items-start gap-4">
                                                <Avatar name={clientName} className="w-10 h-10 mt-1 flex-shrink-0" />
                                                <div className="flex-grow">
                                                    <div className="flex justify-between items-center cursor-pointer" onClick={() => router.push(`/conversations/${msg.client_id}`)}>
                                                        <p className="font-bold hover:underline">{clientName}</p>
                                                        <p className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                                                            <CalendarPlus size={16}/>
                                                            {formatDateTimezone(msg.scheduled_at, effectiveTimezone)}
                                                        </p>
                                                    </div>
                                                    <p className="text-brand-text-muted mt-2 italic">"{msg.content}"</p>
                                                </div>
                                            </div>
                                            <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-white/5">
                                                <Button variant="ghost" size="sm" onClick={() => setEditingMessage(msg)} disabled={!!processingId}><Edit className="w-4 h-4 mr-2" /> Edit</Button>
                                                <Button variant="destructive" size="sm" onClick={() => handleCancel(msg.id)} disabled={!!processingId}>{processingId === msg.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}Cancel</Button>
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </>
    );
};