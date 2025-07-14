// File Path: frontend/components/modals/EditMessageModal.tsx
// --- NEW FILE ---

'use client';

import { useState, FC, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ScheduledMessage, useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Loader2, Save } from 'lucide-react';

interface EditMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: ScheduledMessage | null;
    onSaveSuccess: () => void;
}

export const EditMessageModal: FC<EditMessageModalProps> = ({ isOpen, onClose, message, onSaveSuccess }) => {
    const { api } = useAppContext();
    const [editedContent, setEditedContent] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (message) {
            setEditedContent(message.content);
        }
    }, [message]);

    const handleSave = async () => {
        if (!message) return;
        setIsSaving(true);
        try {
            await api.put(`/api/scheduled-messages/${message.id}`, {
                content: editedContent
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
                <main className="p-6">
                    <textarea
                        value={editedContent}
                        onChange={(e) => setEditedContent(e.target.value)}
                        className="w-full h-40 p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                    />
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