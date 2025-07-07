// frontend/components/conversation/EditMessageModal.tsx
// Purpose: A modal dialog for editing the content and date of a scheduled message.

'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import type { ScheduledMessage } from '@/context/AppContext';

/**
 * Props for the EditMessageModal.
 * @param isOpen - Controls the visibility of the modal.
 * @param onClose - Callback to close the modal.
 * @param message - The scheduled message object to be edited.
 * @param onSave - Callback after a successful save operation.
 * @param api - The API client from AppContext.
 */
interface EditMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: ScheduledMessage | null;
    onSave: (updatedMessage: ScheduledMessage) => void;
    api: any;
}

/**
 * A full-screen modal for editing a scheduled message.
 */
export const EditMessageModal = ({ isOpen, onClose, message, onSave, api }: EditMessageModalProps) => {
    const [content, setContent] = useState('');
    const [scheduledAt, setScheduledAt] = useState('');

    // Pre-fill the form when a message is passed in.
    useEffect(() => {
        if (message) {
            setContent(message.content);
            // Format date for the input type="date" which expects YYYY-MM-DD.
            setScheduledAt(new Date(message.scheduled_at).toISOString().split('T')[0]);
        }
    }, [message]);

    if (!isOpen || !message) return null;

    // Handle the save action.
    const handleSave = async () => {
        try {
            const updatedMessage = await api.put(`/scheduled-messages/${message.id}`, {
                content,
                scheduled_at: new Date(scheduledAt).toISOString()
            });
            onSave(updatedMessage); // Propagate changes to the parent component.
            console.log(`Successfully updated scheduled message: ${message.id}`);
            onClose(); // Close the modal on success.
        } catch(err) {
            console.error("Failed to save scheduled message:", err);
            alert("Failed to save changes.");
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-brand-dark border border-white/10 rounded-2xl w-full max-w-2xl flex flex-col shadow-2xl">
                <header className="p-6 border-b border-white/10 flex justify-between items-center">
                    <h2 className="text-xl font-bold text-white">Edit Scheduled Message</h2>
                    <button onClick={onClose} className="p-2 rounded-full hover:bg-white/10">
                        <X size={20} />
                    </button>
                </header>
                <main className="p-6 space-y-4">
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted mb-2 block">Scheduled Date</label>
                        <input
                            type="date"
                            value={scheduledAt}
                            onChange={e => setScheduledAt(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted mb-2 block">Message Content</label>
                        <textarea
                            value={content}
                            onChange={e => setContent(e.target.value)}
                            rows={6}
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
                        />
                    </div>
                </main>
                <footer className="p-6 border-t border-white/10 flex justify-end gap-4">
                    <button onClick={onClose} className="px-5 py-2.5 text-sm font-semibold bg-white/10 hover:bg-white/20 rounded-md">Cancel</button>
                    <button onClick={handleSave} className="px-5 py-2.5 text-sm font-semibold bg-primary-action text-brand-dark hover:brightness-110 rounded-md">Save Changes</button>
                </footer>
            </div>
        </div>
    );
};