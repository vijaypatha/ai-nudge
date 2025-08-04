// frontend/components/nudges/ScheduledNudgesView.tsx
// --- FINAL, CORRECTED VERSION ---

'use client';

import { FC, useMemo, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Client, ScheduledMessage, useAppContext, User } from '@/context/AppContext';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { EditMessageModal } from '@/components/modals/EditMessageModal';
import { CalendarClock, Loader2, Edit, Trash2 } from 'lucide-react';
import { formatInTimeZone } from 'date-fns-tz';
import { parseISO } from 'date-fns';

interface ScheduledNudgesViewProps {
    messages: ScheduledMessage[];
    isLoading: boolean;
    clients: Client[];
    user: User | null;
    onAction: () => void;
}

/**
 * Safely parses a "YYYY-MM-DD HH:mm:ss" UTC string from the database.
 * Converts it to a valid ISO 8601 format ("YYYY-MM-DDTHH:mm:ssZ") before parsing
 * to prevent JavaScript from incorrectly interpreting it as local time.
 * @param utcString The UTC datetime string from the backend.
 * @returns A valid Date object.
 */
const parseSafeUTCSring = (utcString: string | undefined | null): Date => {
    if (!utcString) return new Date(NaN); // Return an invalid date for null/undefined input
    return parseISO(utcString.replace(' ', 'T') + 'Z');
};

const groupMessagesByDate = (messages: ScheduledMessage[], localTimeZone: string) => {
    const groups: { [key: string]: ScheduledMessage[] } = { Today: [], Tomorrow: [], 'This Week': [], 'Later': [] };
    const todayStr = formatInTimeZone(new Date(), localTimeZone, 'yyyy-MM-dd');

    messages.forEach(msg => {
        const scheduledDate = parseSafeUTCSring(msg.scheduled_at_utc);
        if (isNaN(scheduledDate.getTime())) return; // Skip messages with invalid dates

        const msgDateStr = formatInTimeZone(scheduledDate, localTimeZone, 'yyyy-MM-dd');
        // Safely calculate day difference from date strings to avoid timezone shifts
        const diffDays = Math.round((new Date(msgDateStr).getTime() - new Date(todayStr).getTime()) / 86400000);

        if (diffDays < 0) return; // Ignore past-due messages in this view
        else if (diffDays === 0) groups.Today.push(msg);
        else if (diffDays === 1) groups.Tomorrow.push(msg);
        else if (diffDays > 1 && diffDays <= 7) groups['This Week'].push(msg);
        else groups.Later.push(msg);
    });
    return groups;
};

const formatDisplayDateTime = (utcDateString: string, timeZone: string) => {
    try {
        const date = parseSafeUTCSring(utcDateString);
        if (isNaN(date.getTime())) return "Invalid date";
        return formatInTimeZone(date, timeZone, "MMM d, h:mm a (zzz)");
    } catch (e) {
        console.error("Timezone formatting failed:", e);
        return utcDateString; // Fallback to original string on error
    }
};

export const ScheduledNudgesView: FC<ScheduledNudgesViewProps> = ({ messages, isLoading, clients, user, onAction }) => {
    const router = useRouter();
    const { api } = useAppContext();
    const [editingMessage, setEditingMessage] = useState<ScheduledMessage | null>(null);
    const [processingId, setProcessingId] = useState<string | null>(null);

    const userTimezone = user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    const findClient = (clientId: string) => clients.find(c => c.id === clientId);
    
    const pendingMessages = useMemo(() => 
        messages
            .filter(msg => msg.status === 'pending')
            .sort((a, b) => parseSafeUTCSring(a.scheduled_at_utc).getTime() - parseSafeUTCSring(b.scheduled_at_utc).getTime()), 
        [messages]
    );

    const groupedMessages = useMemo(() => groupMessagesByDate(pendingMessages, userTimezone), [pendingMessages, userTimezone]);

    const handleCancel = useCallback(async (messageId: string) => {
        if (!window.confirm("Are you sure you want to cancel this scheduled message?")) return;
        setProcessingId(messageId);
        try {
            await api.del(`/api/scheduled-messages/${messageId}`);
            onAction();
        } catch (error) {
            console.error("Failed to cancel message:", error);
            alert("Could not cancel the message.");
        } finally {
            setProcessingId(null);
        }
    }, [api, onAction]);

    const handleSaveSuccess = () => {
        setEditingMessage(null);
        onAction();
    };

    if (isLoading) {
        return <div className="text-center py-20"><Loader2 className="mx-auto h-12 w-12 animate-spin text-gray-400"/></div>;
    }

    if (pendingMessages.length === 0) {
        return (
            <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
                <CalendarClock className="mx-auto h-16 w-16 text-gray-500" />
                <h3 className="mt-4 text-xl font-medium text-white">Nothing Scheduled</h3>
                <p className="mt-1 text-base text-gray-400">Schedule messages from a conversation or approve an AI-Suggested Plan.</p>
            </div>
        );
    }

    return (
        <>
            {editingMessage && (
                <EditMessageModal 
                    isOpen={!!editingMessage} 
                    onClose={() => setEditingMessage(null)} 
                    message={editingMessage}
                    client={findClient(editingMessage.client_id) ?? null}
                    onSaveSuccess={handleSaveSuccess}
                />
            )}
            <div className="space-y-8 max-w-4xl mx-auto">
                {Object.entries(groupedMessages).map(([groupTitle, groupMessages]) => {
                    if (groupMessages.length === 0) return null;
                    return (
                        <motion.div key={groupTitle} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <h2 className="text-lg font-bold text-white mb-4">{groupTitle} ({groupMessages.length})</h2>
                            <div className="space-y-3">
                                {groupMessages.map(msg => {
                                    const client = findClient(msg.client_id);
                                    return (
                                        <motion.div 
                                            key={msg.id} 
                                            className="bg-brand-primary border border-white/10 rounded-xl p-4 transition-all hover:border-white/20"
                                            layout
                                        >
                                            <div className="flex items-start gap-4">
                                                <Avatar name={client?.full_name || '...'} className="w-10 h-10 mt-1 flex-shrink-0" />
                                                <div className="flex-grow">
                                                    <div className="flex justify-between items-center">
                                                        <p 
                                                            className="font-bold hover:underline cursor-pointer text-white"
                                                            onClick={() => router.push(`/conversations/${msg.client_id}`)}
                                                        >
                                                            {client?.full_name || 'Unknown Client'}
                                                        </p>
                                                        <p className="text-sm font-semibold text-cyan-400">
                                                            {formatDisplayDateTime(msg.scheduled_at_utc, msg.timezone || userTimezone)}
                                                        </p>
                                                    </div>
                                                    <p className="text-gray-300 mt-2 italic">"{msg.content}"</p>
                                                </div>
                                            </div>
                                            <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-white/5">
                                                <Button variant="ghost" size="sm" onClick={() => setEditingMessage(msg)} disabled={!!processingId}>
                                                    <Edit className="w-4 h-4 mr-2" /> Edit
                                                </Button>
                                                <Button variant="destructive" size="sm" onClick={() => handleCancel(msg.id)} disabled={!!processingId}>
                                                    {processingId === msg.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Trash2 className="w-4 h-4 mr-2" />Cancel</>}
                                                </Button>
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