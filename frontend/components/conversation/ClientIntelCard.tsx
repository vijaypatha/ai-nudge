// frontend/components/conversation/ClientIntelCard.tsx
// --- DEFINITIVE, COMPLETE VERSION ---

'use client';

import { useState, useEffect } from 'react';
import { Info, Sparkles, Edit, Save, Loader2 } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { TimezoneSelector } from '../ui/TimezoneSelector';

interface ClientIntelCardProps {
    client: Client | undefined;
    onUpdate: (updatedClient: Client) => void;
    onReplan: () => void;
}

export const ClientIntelCard = ({ client, onUpdate, onReplan }: ClientIntelCardProps) => {
    const { api } = useAppContext();
    const [isEditing, setIsEditing] = useState(false);
    const [notes, setNotes] = useState('');
    const [timezone, setTimezone] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [showReplanPrompt, setShowReplanPrompt] = useState(false);

    useEffect(() => {
        if (client) {
            setNotes(client.notes || '');
            setTimezone(client.timezone || '');
        }
    }, [client]);

    if (!client) return null;

    const handleSave = async () => {
        setIsSaving(true);
        try {
            // --- MODIFIED: Build the payload dynamically ---
            // This is a more robust pattern that only sends changed data,
            // which can prevent issues with how the backend processes null/empty values.
            const payload: { notes?: string; timezone?: string | null } = {};
    
            if (notes !== (client.notes || '')) {
                payload.notes = notes;
            }
            if (timezone !== (client.timezone || '')) {
                payload.timezone = timezone || null;
            }
    
            // Only make an API call if there's actually something to save.
            if (Object.keys(payload).length > 0) {
                const updatedClient = await api.put(`/api/clients/${client.id}`, payload);
                onUpdate(updatedClient);
            }
            
            setIsEditing(false);
            // We only show the replan prompt if notes actually changed.
            if (payload.notes !== undefined) {
                setShowReplanPrompt(true);
            }
    
        } catch(err) {
            console.error("Failed to save client intel:", err);
            alert("Failed to save intel.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setIsEditing(false);
        setNotes(client.notes || '');
        setTimezone(client.timezone || '');
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
    
    const renderedNotesContent = renderNotes(client?.notes);
    const hasVisibleNotes = renderedNotesContent && renderedNotesContent.some(item => item);

    return (
        <InfoCard title="Client Intel" icon={<Info size={14}/>} onEdit={!isEditing ? () => setIsEditing(true) : undefined}>
            <div className="pt-2">
                {isEditing ? (
                    <div className="space-y-4">
                         <div>
                            <label className="text-xs font-semibold text-gray-400 mb-1 block">Time Zone Override</label>
                            <TimezoneSelector value={timezone} onChange={e => setTimezone(e.target.value)} />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-gray-400 mb-1 block">Notes</label>
                            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={5} className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm" />
                        </div>
                        <div className="flex gap-2 justify-end">
                            <button onClick={handleCancel} className="px-3 py-1 text-xs font-semibold bg-white/10 rounded-md">Cancel</button>
                            <button onClick={handleSave} disabled={isSaving} className="px-3 py-1 text-xs font-semibold bg-primary-action text-brand-dark rounded-md flex items-center gap-1.5">
                               {isSaving ? <Loader2 className="h-4 w-4 animate-spin"/> : <Save size={14}/>} Save
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div>
                            <h4 className="text-xs font-bold text-gray-500 uppercase mb-1">TIMEZONE</h4>
                            <p className="text-sm text-gray-200">{client.timezone || 'Using your default'}</p>
                        </div>
                         <div>
                            <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">NOTES</h4>
                            {hasVisibleNotes ? (
                                <ul className="space-y-2 pl-1">{renderedNotesContent}</ul>
                            ) : (
                                <p className="text-xs text-brand-text-muted text-center py-2">No intel added. Click the edit icon to add notes.</p>
                            )}
                        </div>
                    </div>
                )}
                {showReplanPrompt && (
                    <div className="mt-4 p-3 bg-primary-action/10 rounded-lg text-center space-y-2 border border-primary-action/20">
                        <p className="text-sm font-semibold text-brand-accent">Update the Relationship Campaign with this new information?</p>
                        <div className="flex gap-2 justify-center">
                            <button onClick={() => setShowReplanPrompt(false)} className="px-3 py-1 text-xs bg-white/10 rounded-md">No, Thanks</button>
                            <button onClick={() => { onReplan(); setShowReplanPrompt(false); }} className="px-3 py-1 text-xs bg-primary-action text-brand-dark rounded-md">Yes, Update</button>
                        </div>
                    </div>
                )}
            </div>
        </InfoCard>
    );
};