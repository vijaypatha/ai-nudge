// frontend/components/conversation/ClientIntelCard.tsx
// --- REVISED: Now fully agnostic, driven by displayConfig prop. ---

'use client';

import { useState, useEffect, ReactNode } from 'react';
import { Info, Sparkles, Edit, Save, Loader2, DollarSign, BedDouble, Bath, MapPin, BrainCircuit, HeartHandshake } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { TimezoneSelector } from '../ui/TimezoneSelector';

// --- NEW: Define a type for preference metadata, expected from displayConfig ---
interface PreferenceMeta {
  label: string;
  icon: string; // Icon name as a string
  type?: 'text' | 'number' | 'textarea';
  format?: (value: any) => string;
}

// --- NEW: A central place to map icon names to actual components ---
const ICON_MAP: Record<string, ReactNode> = {
    Info: <Info size={14} />,
    Default: <Info size={14} />,
    DollarSign: <DollarSign size={12} />,
    BedDouble: <BedDouble size={12} />,
    Bath: <Bath size={12} />,
    MapPin: <MapPin size={12} />,
    BrainCircuit: <BrainCircuit size={12} />,
    HeartHandshake: <HeartHandshake size={12} />,
};

// This would be defined in a shared types file or passed from the parent
export interface ConversationDisplayConfig {
  client_intel: {
    title: string;
    icon: string;
    preferences?: Record<string, PreferenceMeta>;
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

    // --- MODIFIED: Use a default empty config to prevent errors ---
    const intelConfig = displayConfig?.client_intel || { title: 'Client Intel', icon: 'Default', preferences: {} };
    const cardIcon = ICON_MAP[intelConfig.icon] || ICON_MAP.Default;

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
            const payload: any = {};
            if (notes !== (client.notes || '')) payload.notes_to_add = notes;
            if (timezone !== (client.timezone || '')) payload.timezone = timezone || null;
            
            // Don't send preferences directly - let the profiler extract them from notes
            // The profiler will analyze the notes and extract new preferences dynamically

            if (Object.keys(payload).length > 0) {
                // Call the intel endpoint that triggers the profiler
                const updatedClient = await api.post(`/api/clients/${client.id}/intel`, payload);
                onUpdate(updatedClient);
                if (payload.notes_to_add !== undefined) setShowReplanPrompt(true);
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
    
    // --- MODIFIED: This function now displays any preferences that exist ---
    const renderPreferences = (prefs: Client['preferences']) => {
        if (!prefs || Object.keys(prefs).length === 0) return null;

        // Helper function to format values
        const formatValue = (value: any): string => {
            if (value === null || value === undefined) return '';
            if (typeof value === 'number') {
                // Check if it looks like currency (large numbers)
                if (value > 1000) {
                    return `$${value.toLocaleString()}`;
                }
                return value.toString();
            }
            if (Array.isArray(value)) {
                return value.join(', ');
            }
            return String(value);
        };

        // Helper function to format keys for display
        const formatKey = (key: string): string => {
            return key
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase())
                .replace(/\b(max|min)\b/g, (match) => match === 'max' ? 'Max' : 'Min');
        };

        return (
            <div className="grid grid-cols-2 gap-x-4 gap-y-3 mt-1">
                {Object.entries(prefs).map(([key, value]) => {
                    if (!value && value !== 0) return null; // Skip empty values
                    
                    const displayValue = formatValue(value);
                    const displayKey = formatKey(key);
                    
                    return (
                        <div key={key} className="text-sm">
                            <dt className="text-xs text-brand-text-muted flex items-center gap-1.5">
                                <Info size={12} /> {displayKey}
                            </dt>
                            <dd className="font-medium text-brand-text-main pl-[22px]">{displayValue}</dd>
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
        <InfoCard title={intelConfig.title} icon={cardIcon} onEdit={!isEditing ? () => setIsEditing(true) : undefined}>
            <div className="pt-2">
                {isEditing ? (
                    <div className="space-y-4">
                        <div>
                            <label className="text-xs font-semibold text-gray-400 mb-1 block">Time Zone</label>
                            <TimezoneSelector value={timezone} onChange={e => setTimezone(e.target.value)} />
                        </div>
                        
                        {/* --- MODIFIED: Edit form is now dynamically generated from actual preferences --- */}
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries(client?.preferences || {}).map(([key, value]) => {
                                const displayKey = key
                                    .replace(/_/g, ' ')
                                    .replace(/\b\w/g, l => l.toUpperCase())
                                    .replace(/\b(max|min)\b/g, (match) => match === 'max' ? 'Max' : 'Min');
                                
                                return (
                                    <div key={key}>
                                        <label className="text-xs font-semibold text-gray-400 mb-1 block">{displayKey}</label>
                                        <input 
                                            type={typeof value === 'number' ? 'number' : 'text'}
                                            placeholder={`e.g., ${displayKey}`}
                                            value={preferences[key] || ''} 
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