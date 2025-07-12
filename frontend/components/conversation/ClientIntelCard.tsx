// frontend/components/conversation/ClientIntelCard.tsx
// --- DEFINITIVE FIX: Simplified rendering logic to resolve TypeScript errors permanently.

'use client';

import { useState, useEffect } from 'react';
import { Info, Sparkles } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';

interface ClientIntelCardProps {
    client: Client | undefined;
    onUpdate: (updatedClient: Client) => void;
    onReplan: () => void;
}

export const ClientIntelCard = ({ client, onUpdate, onReplan }: ClientIntelCardProps) => {
    const { api } = useAppContext();
    const [isEditing, setIsEditing] = useState(false);
    const [notes, setNotes] = useState('');
    const [showReplanPrompt, setShowReplanPrompt] = useState(false);

    useEffect(() => {
        if (client) {
            setNotes(client.notes || '');
        }
    }, [client]);

    if (!client) return null;

    const handleSave = async () => {
        try {
            const updatedClient = await api.put(`/api/clients/${client.id}/notes`, { notes: notes });
            onUpdate(updatedClient);
            setIsEditing(false);
            setShowReplanPrompt(true);
            console.log(`Successfully saved intel for client: ${client.id}`);
        } catch(err) {
            console.error("Failed to save client intel:", err);
            alert("Failed to save intel.");
        }
    };

    const handleReplan = () => {
        onReplan();
        setShowReplanPrompt(false);
    };

    const renderNotes = (text: string | null | undefined) => {
        if (!text) return null;
        
        return text.split('\n').map((line, index) => (
            line.trim() && (
                <li key={index} className="flex items-start gap-3 text-sm">
                    <Sparkles size={14} className="flex-shrink-0 mt-0.5 text-brand-accent" />
                    {line}
                </li>
            )
        ));
    };

    // --- NEW LOGIC START ---
    // Pre-calculate the notes content and whether it has visible items.
    // This simplifies the JSX and resolves the TypeScript error.
    const renderedNotesContent = renderNotes(client?.notes);
    const hasVisibleNotes = renderedNotesContent && renderedNotesContent.some(item => item);
    // --- NEW LOGIC END ---

    return (
        <InfoCard title="Client Intel" icon={<Info size={14}/>} onEdit={!isEditing ? () => setIsEditing(true) : undefined}>
            <div className="pt-2">
                {isEditing ? (
                    <div className="space-y-3">
                        <p className="text-xs text-brand-text-muted">Enter each piece of intel on a new line.</p>
                        <textarea
                            value={notes}
                            onChange={e => setNotes(e.target.value)}
                            rows={5}
                            className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm"
                        />
                        <div className="flex gap-2 justify-end">
                            <button onClick={() => { setIsEditing(false); setNotes(client.notes || ''); }} className="px-3 py-1 text-xs font-semibold bg-white/10 rounded-md">Cancel</button>
                            <button onClick={handleSave} className="px-3 py-1 text-xs font-semibold bg-primary-action text-brand-dark rounded-md">Save Intel</button>
                        </div>
                    </div>
                ) : (
                    <ul className="space-y-2">
                        {/* --- MODIFIED JSX START --- */}
                        {/* This logic is now much cleaner and uses the pre-calculated variables. */}
                        {hasVisibleNotes ? (
                            renderedNotesContent
                        ) : (
                            <p className="text-xs text-brand-text-muted text-center py-2">No intel added. Click the edit icon to add notes.</p>
                        )}
                        {/* --- MODIFIED JSX END --- */}
                    </ul>
                )}
                {showReplanPrompt && (
                    <div className="mt-4 p-3 bg-primary-action/10 rounded-lg text-center space-y-2 border border-primary-action/20">
                        <p className="text-sm font-semibold text-brand-accent">Update the Relationship Campaign with this new information?</p>
                        <div className="flex gap-2 justify-center">
                            <button onClick={() => setShowReplanPrompt(false)} className="px-3 py-1 text-xs bg-white/10 rounded-md">No, Thanks</button>
                            <button onClick={handleReplan} className="px-3 py-1 text-xs bg-primary-action text-brand-dark rounded-md">Yes, Update</button>
                        </div>
                    </div>
                )}
            </div>
        </InfoCard>
    );
};