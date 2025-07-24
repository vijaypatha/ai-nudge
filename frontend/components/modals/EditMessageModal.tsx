// frontend/components/modals/EditMessageModal.tsx
'use client';

import { useState, FC, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Client, ScheduledMessage, useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Loader2, Save, Edit3 } from 'lucide-react';
import { formatInTimeZone, getTimezoneOffset } from 'date-fns-tz';

interface EditMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: ScheduledMessage | null;
    onSaveSuccess: () => void;
    // --- NEW: Pass the full client object for timezone info ---
    client: Client | null;
}

export const EditMessageModal: FC<EditMessageModalProps> = ({ isOpen, onClose, message, onSaveSuccess, client }) => {
    const { api } = useAppContext();
    const [content, setContent] = useState('');
    const [localDate, setLocalDate] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    // --- NEW: Determine the correct timezone to use ---
    const targetTimezone = client?.timezone || message?.timezone || 'UTC';
    const timezoneAbbr = new Date().toLocaleTimeString('en-us', { timeZone: targetTimezone, timeZoneName: 'short' }).split(' ')[2];

    useEffect(() => {
        if (message) {
            setContent(message.content);
            // Convert the stored UTC time back to the client's local time for the input
            const scheduledTimeInTargetTZ = formatInTimeZone(message.scheduled_at_utc, targetTimezone, "yyyy-MM-dd'T'HH:mm");
            setLocalDate(scheduledTimeInTargetTZ);
        }
    }, [message, targetTimezone]);

    const handleSave = async () => {
        if (!message || !content || !localDate) return;
        setIsSaving(true);
        try {
            await api.put(`/api/scheduled-messages/${message.id}`, {
                content,
                // --- MODIFIED: Always send the client's timezone context ---
                scheduled_at_local: localDate,
                timezone: targetTimezone,
            });
            onSaveSuccess();
        } catch (error) {
            console.error("Failed to save message:", error);
            alert("Could not save changes. Please try again.");
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen || !message) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-brand-primary border border-white/10 rounded-xl shadow-lg w-full max-w-lg flex flex-col"
            >
                <header className="flex items-center justify-between p-4 border-b border-white/10">
                    <h2 className="font-bold text-lg text-white">Edit Scheduled Message</h2>
                    <Button variant="ghost" size="sm" onClick={onClose}><X className="w-5 h-5" /></Button>
                </header>
                <main className="p-6 space-y-4">
                    <div>
                        <label className="text-sm font-semibold text-gray-300 mb-2 block">Message</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            className="w-full h-32 p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                        />
                    </div>
                    <div>
                        <label className="text-sm font-semibold text-gray-300 mb-2 block">Date & Time</label>
                        <input
                            type="datetime-local"
                            value={localDate}
                            onChange={(e) => setLocalDate(e.target.value)}
                            className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                        />
                         {/* --- NEW: Confirmation Text --- */}
                         <p className="text-xs text-gray-400 mt-2">
                            Sends at the selected time in the client's local timezone ({timezoneAbbr}).
                            <a href={`/conversations/${client?.id}`} className="underline ml-1 hover:text-white">Edit client timezone</a>.
                        </p>
                    </div>
                </main>
                <footer className="flex justify-end gap-3 p-4 bg-black/20 border-t border-white/10">
                    <Button variant="secondary" onClick={onClose} disabled={isSaving}>Cancel</Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                        Save Changes
                    </Button>
                </footer>
            </motion.div>
        </div>
    );
};