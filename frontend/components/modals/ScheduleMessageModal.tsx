// frontend/components/modals/ScheduleMessageModal.tsx
'use client';

import { useState, FC, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { TimezoneSelector } from '@/components/ui/TimezoneSelector';
import { X, Loader2, CalendarClock } from 'lucide-react';

interface ScheduleMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    onScheduleSuccess: () => void;
    clientId: string;
    initialContent?: string;
}

export const ScheduleMessageModal: FC<ScheduleMessageModalProps> = ({ isOpen, onClose, onScheduleSuccess, clientId, initialContent = '' }) => {
    const { api, user } = useAppContext();
    const [content, setContent] = useState('');
    const [date, setDate] = useState('');
    const [timezone, setTimezone] = useState(user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (isOpen) {
            // Set default time to 30 mins in the future
            const futureDate = new Date(Date.now() + 30 * 60 * 1000);
            const localISOString = new Date(futureDate.getTime() - (futureDate.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
            setDate(localISOString);
            setContent(initialContent); // Use initial content if provided
        }
    }, [isOpen, initialContent]);

    const handleSchedule = async () => {
        if (!content || !date || !timezone || !clientId) {
            alert("Please fill out all fields.");
            return;
        }
        setIsSaving(true);
        try {
            // The backend expects the local datetime string and a separate timezone string.
            await api.post(`/api/scheduled-messages`, {
                client_id: clientId,
                content: content,
                scheduled_at_local: date,
                timezone: timezone,
            });
            onScheduleSuccess();
        } catch (error) {
            console.error("Failed to schedule message:", error);
            alert("Could not schedule the message. Please try again.");
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-brand-primary border border-white/10 rounded-xl shadow-lg w-full max-w-lg flex flex-col"
            >
                <header className="flex items-center justify-between p-4 border-b border-white/10">
                    <h2 className="font-bold text-lg text-white">Schedule a Message</h2>
                    <Button variant="ghost" size="sm" onClick={onClose}><X className="w-5 h-5" /></Button>
                </header>
                <main className="p-6 space-y-4">
                    <div>
                        <label className="text-sm font-semibold text-gray-300 mb-2 block">Message</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            className="w-full h-32 p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                            placeholder="Write your message here..."
                        />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                         <div>
                            <label className="text-sm font-semibold text-gray-300 mb-2 block">Date & Time</label>
                            <input
                                type="datetime-local"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-semibold text-gray-300 mb-2 block">Time Zone</label>
                            <TimezoneSelector
                                value={timezone}
                                onChange={(e) => setTimezone(e.target.value)}
                                className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                            />
                        </div>
                    </div>
                </main>
                <footer className="flex justify-end gap-3 p-4 bg-black/20 border-t border-white/10">
                    <Button variant="secondary" onClick={onClose} disabled={isSaving}>Cancel</Button>
                    <Button onClick={handleSchedule} disabled={isSaving || !content || !date || !timezone}>
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CalendarClock className="w-4 h-4 mr-2" />}
                        Schedule Message
                    </Button>
                </footer>
            </motion.div>
        </div>
    );
};