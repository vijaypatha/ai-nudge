// frontend/components/conversation/ClientIntelCard.tsx
// Purpose: A specific implementation of InfoCard for managing client notes and preferences.

'use client';

import { useState, useEffect } from 'react';
import { Info, Sparkles } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';

/**
 * Props for the ClientIntelCard.
 * @param client - The client object whose intel is being displayed.
 * @param onUpdate - Callback to update the client list after a change.
 * @param onReplan - Callback to trigger a campaign replan after intel changes.
 */
interface ClientIntelCardProps {
    client: Client | undefined;
    onUpdate: (updatedClient: Client) => void;
    onReplan: () => void;
}

/**
 * Displays and allows editing of client "intel" (notes and preferences).
 * Prompts the user to replan the relationship campaign if intel is updated.
 */
export const ClientIntelCard = ({ client, onUpdate, onReplan }: ClientIntelCardProps) => {
    const { api } = useAppContext();
    const [isEditing, setIsEditing] = useState(false);
    const [notes, setNotes] = useState('');
    const [showReplanPrompt, setShowReplanPrompt] = useState(false);

    // Effect to reset notes when the client changes or editing is cancelled.
    useEffect(() => {
        if (client) {
            setNotes(client.preferences?.notes?.join('\n') || '');
        }
    }, [client]);

    if (!client) return null; // Don't render if no client is selected

    const handleSave = async () => {
        // Prepare the updated preferences object.
        const updatedPreferences = { ...client.preferences, notes: notes.split('\n').filter(n => n.trim()) };
        try {
            // API call to update the client's preferences.
            const updatedClient = await api.put(`/clients/${client.id}`, { preferences: updatedPreferences });
            onUpdate(updatedClient); // Update client in the global context.
            setIsEditing(false); // Exit editing mode.
            setShowReplanPrompt(true); // Show prompt to update campaign.
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
                            <button onClick={() => { setIsEditing(false); setNotes(client.preferences?.notes?.join('\n') || ''); }} className="px-3 py-1 text-xs font-semibold bg-white/10 rounded-md">Cancel</button>
                            <button onClick={handleSave} className="px-3 py-1 text-xs font-semibold bg-primary-action text-brand-dark rounded-md">Save Intel</button>
                        </div>
                    </div>
                ) : (
                    <ul className="space-y-2">
                        {(client.preferences?.notes || []).length > 0 ? (
                            (client.preferences?.notes || []).map((note: string, index: number) => (
                                <li key={index} className="flex items-start gap-3 text-sm">
                                    <Sparkles size={14} className="flex-shrink-0 mt-0.5 text-brand-accent" />
                                    {note}
                                </li>
                            ))
                        ) : (
                            <p className="text-xs text-brand-text-muted text-center py-2">No intel added. Click the edit icon to add notes.</p>
                        )}
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