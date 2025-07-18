// frontend/components/modals/EditMessageModal.tsx
// --- FINAL, CORRECTED VERSION ---
// This version uses the correct 'scheduled_at_utc' property and provides full editing functionality.

'use client';

import { useState, FC, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ScheduledMessage, useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { TimezoneSelector } from '@/components/ui/TimezoneSelector';
import { X, Loader2, Save } from 'lucide-react';
import { formatInTimeZone } from 'date-fns-tz';

interface EditMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: ScheduledMessage | null;
    onSaveSuccess: () => void;
}

export const EditMessageModal: FC<EditMessageModalProps> = ({ isOpen, onClose, message, onSaveSuccess }) => {
    const { api } = useAppContext();
    const [content, setContent] = useState('');
    const [localDate, setLocalDate] = useState('');
    const [timezone, setTimezone] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (message) {
            setContent(message.content);
            setTimezone(message.timezone);

            // --- THE FIX IS HERE ---
            // This now correctly uses 'message.scheduled_at_utc' which exists on the type.
            // The previous code was still referencing 'message.scheduled_at', causing the build to fail.
            const scheduledTimeInOriginalTZ = formatInTimeZone(message.scheduled_at_utc, message.timezone, "yyyy-MM-dd'T'HH:mm");
            setLocalDate(scheduledTimeInOriginalTZ);
        }
    }, [message]);

    const handleSave = async () => {
        if (!message || !content || !localDate || !timezone) return;
        setIsSaving(true);
        try {
            // The API call correctly sends the local date string and the timezone.
            await api.put(`/api/scheduled-messages/${message.id}`, {
                content,
                scheduled_at_local: localDate,
                timezone: timezone,
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
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-semibold text-gray-300 mb-2 block">Date & Time</label>
                            <input
                                type="datetime-local"
                                value={localDate}
                                onChange={(e) => setLocalDate(e.target.value)}
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
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                        Save Changes
                    </Button>
                </footer>
            </motion.div>
        </div>
    );
};