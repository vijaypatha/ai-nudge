// frontend/components/conversation/EditMessageModal.tsx

'use client';

import { useState, useEffect } from 'react';
import { ScheduledMessage, useAppContext } from '@/context/AppContext';
import { Button } from '../ui/Button';

interface EditMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: ScheduledMessage;
}

export const EditMessageModal = ({ isOpen, onClose, message }: EditMessageModalProps) => {
    const { api, refetchScheduledMessagesForClient } = useAppContext();
    const [content, setContent] = useState(message.content);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        setContent(message.content);
    }, [message]);

    if (!isOpen) return null;

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await api.put(`/api/scheduled-messages/${message.id}`, {
                content: content,
            });
            // Refetch scheduled messages for the client to update the UI
            await refetchScheduledMessagesForClient(message.client_id);
            onClose();
        } catch (error) {
            console.error("Failed to save changes:", error);
            alert("Failed to save changes.");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
            <div className="bg-brand-dark-blue border border-white/10 rounded-lg shadow-2xl w-full max-w-lg m-4">
                <div className="p-6 border-b border-white/10 flex justify-between items-center">
                    <h2 className="text-lg font-semibold text-white">Edit Scheduled Message</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">&times;</button>
                </div>
                <div className="p-6 space-y-4">
                    <div>
                        <label className="text-sm font-medium text-gray-400 block mb-2">Scheduled Date</label>
                        <input
                            type="text"
                            readOnly
                            value={new Date(message.scheduled_at_utc).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                            className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm text-gray-300"
                        />
                    </div>
                    <div>
                        <label className="text-sm font-medium text-gray-400 block mb-2">Message Content</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            rows={6}
                            className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm text-white"
                        />
                    </div>
                </div>
                <div className="p-6 bg-black/20 rounded-b-lg flex justify-end gap-3">
                    <Button variant="secondary" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                </div>
            </div>
        </div>
    );
};