// frontend/components/conversation/ClientIntelCard.tsx
// --- FINAL FIX: Sends a correctly typed payload to the standard update endpoint ---

'use client';

import { useState, useEffect, ReactNode } from 'react';
import { Info, Sparkles, Edit, Save, Loader2 } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { TimezoneSelector } from '../ui/TimezoneSelector';

// This is defined locally to match the backend's `ClientUpdate` model
// without assuming a shared file structure.
interface ClientUpdatePayload {
    notes?: string;
    preferences?: { [key: string]: any; };
    timezone?: string | null;
}

// This would be defined in a shared types file or passed from the parent
export interface ConversationDisplayConfig {
  client_intel: {
    title: string;
    icon: string;
  };
}

interface ClientIntelCardProps {
    client: Client | undefined;
    onUpdate: (updatedClient: Client) => void;
    onReplan: () => void;
    displayConfig: ConversationDisplayConfig | null;
}

export const ClientIntelCard = ({ client, onUpdate, onReplan, displayConfig }: ClientIntelCardProps) => {
    const { api } = useAppContext();
    const [isEditing, setIsEditing] = useState(false);
    const [notes, setNotes] = useState('');
    const [preferences, setPreferences] = useState<Client['preferences']>({});
    const [timezone, setTimezone] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [showReplanPrompt, setShowReplanPrompt] = useState(false);

    const intelConfig = displayConfig?.client_intel || { title: 'Client Intel', icon: 'Info' };

    useEffect(() => {
        if (client) {
            setNotes(client.notes || '');
            setPreferences(client.preferences || {});
            setTimezone(client.timezone || '');
        }
    }, [client]);

    if (!client) return null;

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const payload: ClientUpdatePayload = {};
            const originalClient = client;

            // 1. Check if preferences have changed
            if (JSON.stringify(preferences) !== JSON.stringify(originalClient.preferences || {})) {
                const sanitizedPrefs: { [key: string]: any; } = {};
                for (const [key, value] of Object.entries(preferences)) {
                     // Convert string inputs from form back to numbers if original was a number
                    if (typeof originalClient.preferences?.[key] === 'number') {
                        sanitizedPrefs[key] = Number(value) || null;
                    } else {
                        sanitizedPrefs[key] = value;
                    }
                }
                payload.preferences = sanitizedPrefs;
            }
            
            // 2. Check if notes have changed
            if (notes !== (originalClient.notes || '')) {
                payload.notes = notes;
            }

            // 3. Check if timezone has changed
            if (timezone !== (originalClient.timezone || '')) {
                payload.timezone = timezone || null;
            }
            
            // 4. Only send an update if something has actually changed
            if (Object.keys(payload).length > 0) {
                // Use the generic PUT endpoint for updating client data
                const updatedClient = await api.put(`/api/clients/${client.id}`, payload);
                onUpdate(updatedClient);
                if (payload.notes !== undefined || payload.preferences !== undefined) {
                    setShowReplanPrompt(true);
                }
            }
            
            setIsEditing(false);
           
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
        setPreferences(client.preferences || {});
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
    
    const renderPreferences = (prefs: Client['preferences']) => {
        if (!prefs || Object.keys(prefs).length === 0) return null;

        const formatValue = (value: any): string => {
            if (value === null || value === undefined) return '';
            if (typeof value === 'number') {
                if (value > 1000) return `$${value.toLocaleString()}`;
                return value.toString();
            }
            if (Array.isArray(value)) return value.join(', ');
            return String(value);
        };

        const formatKey = (key: string): string => {
            return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()).replace(/\b(max|min)\b/g, match => match.charAt(0).toUpperCase() + match.slice(1));
        };

        return (
            <div className="grid grid-cols-2 gap-x-4 gap-y-3 mt-1">
                {Object.entries(prefs).map(([key, value]) => {
                    if (value === null || value === '' || (Array.isArray(value) && value.length === 0)) return null;
                    return (
                        <div key={key} className="text-sm">
                            <dt className="text-xs text-brand-text-muted flex items-center gap-1.5">
                                <Info size={12} /> {formatKey(key)}
                            </dt>
                            <dd className="font-medium text-brand-text-main pl-[22px]">{formatValue(value)}</dd>
                        </div>
                    );
                })}
            </div>
        );
    };

    const renderedNotesContent = renderNotes(client?.notes);
    const hasVisibleNotes = renderedNotesContent && renderedNotesContent.some(item => item);
    const renderedPreferencesContent = renderPreferences(client?.preferences);

    return (
        <InfoCard title={intelConfig.title} icon={<Info size={14} />} onEdit={!isEditing ? () => setIsEditing(true) : undefined}>
            <div className="pt-2">
                {isEditing ? (
                    <div className="space-y-4">
                        <div>
                            <label className="text-xs font-semibold text-gray-400 mb-1 block">Time Zone</label>
                            <TimezoneSelector value={timezone} onChange={e => setTimezone(e.target.value)} />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries(preferences).map(([key, value]) => {
                                const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()).replace(/\b(max|min)\b/g, match => match.charAt(0).toUpperCase() + match.slice(1));
                                return (
                                    <div key={key}>
                                        <label className="text-xs font-semibold text-gray-400 mb-1 block">{displayKey}</label>
                                        <input 
                                            type={typeof client?.preferences?.[key] === 'number' ? 'number' : 'text'}
                                            placeholder={`e.g., ${displayKey}`}
                                            value={value || ''} 
                                            onChange={(e) => setPreferences(p => ({...p, [key]: e.target.value}))} 
                                            className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm"
                                        />
                                    </div>
                                );
                            })}
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
                            <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">PREFERENCES</h4>
                            {renderedPreferencesContent ? (
                                renderedPreferencesContent
                            ) : (
                                !hasVisibleNotes && <p className="text-xs text-brand-text-muted text-center py-2">No intel added. Click the edit icon to add details.</p>
                            )}
                        </div>
                         {hasVisibleNotes && (
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">NOTES</h4>
                                <ul className="space-y-2 pl-1">{renderedNotesContent}</ul>
                            </div>
                         )}
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