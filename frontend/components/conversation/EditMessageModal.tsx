// frontend/components/modals/EditMessageModal.tsx
// --- FINAL, CORRECTED VERSION ---

'use client';

import { useState, useEffect, FC } from 'react';
import { ScheduledMessage, useAppContext } from '@/context/AppContext';
import { Button } from '../ui/Button';
import { Loader2, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { formatInTimeZone } from 'date-fns-tz';
import { parseISO } from 'date-fns';

interface EditMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: ScheduledMessage;
    onSaveSuccess: () => void; // This prop is now correctly defined
}

export const EditMessageModal: FC<EditMessageModalProps> = ({ isOpen, onClose, message, onSaveSuccess }) => {
    const { api } = useAppContext();
    const [content, setContent] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (message) {
            setContent(message.content);
        }
    }, [message]);

    if (!isOpen) return null;

    const handleSave = async () => {
        if (!content.trim()) return;
        setIsSaving(true);
        try {
            await api.put(`/api/scheduled-messages/${message.id}`, {
                content: content,
            });
            onSaveSuccess(); // Notify parent component to refetch data
            onClose();      // Close the modal
        } catch (error) {
            console.error("Failed to save changes:", error);
            alert("Failed to save changes.");
        } finally {
            setIsSaving(false);
        }
    };

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
                        <label className="text-sm font-semibold text-gray-300 mb-2 block">Scheduled For</label>
                        <input
                            type="text"
                            readOnly
                            value={formatInTimeZone(
                                parseISO(message.scheduled_at_utc),
                                message.timezone || 'UTC',
                                'MMM d, yyyy \'at\' h:mm a zzz' // e.g., "Jul 24, 2025 at 3:30 PM MDT"
                            )}
                            className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-gray-300 cursor-default"
                        />
                    </div>
                    <div>
                        <label className="text-sm font-semibold text-gray-300 mb-2 block">Message Content</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            rows={6}
                            className="w-full bg-black/20 border border-white/20 rounded-lg p-3 text-white focus:ring-2 focus:ring-primary-action"
                            placeholder="Write your message here..."
                        />
                    </div>
                </main>
                <footer className="flex justify-end gap-3 p-4 bg-black/20 border-t border-white/10">
                    <Button variant="secondary" onClick={onClose} disabled={isSaving}>Cancel</Button>
                    <Button onClick={handleSave} disabled={isSaving || !content.trim()}>
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
                    </Button>
                </footer>
            </motion.div>
        </div>
    );
};