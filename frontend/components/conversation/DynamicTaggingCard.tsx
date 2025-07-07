// frontend/components/conversation/DynamicTaggingCard.tsx
// Purpose: A card for viewing and managing user-defined and AI-suggested tags for a client.

'use client';

import { useState } from 'react';
import { Tag, BrainCircuit, X, Plus } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';
import { Avatar } from '../ui/Avatar';

/**
 * Props for the DynamicTaggingCard.
 * @param client - The client object whose tags are being managed.
 * @param onUpdate - Callback to update the client list after tags are changed.
 */
interface DynamicTaggingCardProps {
  client: Client;
  onUpdate: (updatedClient: Client) => void;
}

/**
 * Renders a card for adding/removing user tags and viewing AI-suggested tags.
 */
export const DynamicTaggingCard = ({ client, onUpdate }: DynamicTaggingCardProps) => {
    const { api } = useAppContext();
    const [newTag, setNewTag] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    // Generic handler to update tags on the backend.
    const handleUpdateTags = async (updatedUserTags: string[]) => {
        setIsSaving(true);
        try {
            const updatedClient = await api.put(`/clients/${client.id}/tags`, { user_tags: updatedUserTags });
            onUpdate(updatedClient); // Update client in the global context.
            console.log(`Successfully updated tags for client: ${client.id}`);
        } catch (err) {
            console.error("Tag update failed:", err);
            alert("Failed to update tags.");
        } finally {
            setIsSaving(false);
        }
    };

    // Adds a new tag if it's not empty and doesn't already exist.
    const handleAddTag = () => {
        const trimmedTag = newTag.trim();
        if (trimmedTag && !(client.user_tags || []).includes(trimmedTag)) {
            handleUpdateTags([...(client.user_tags || []), trimmedTag]);
            setNewTag(''); // Clear the input field.
        }
    };

    // Removes a specific tag.
    const handleRemoveTag = (tagToRemove: string) => {
        handleUpdateTags((client.user_tags || []).filter(tag => tag !== tagToRemove));
    };

    return (
        <div className="bg-white/5 border border-white/10 rounded-xl">
            {/* Client Header */}
            <div className="p-4 text-center border-b border-white/10">
                <Avatar name={client.full_name} className="w-16 h-16 text-2xl mb-3 mx-auto" />
                <h3 className="text-lg font-bold text-brand-text-main">{client.full_name}</h3>
                <p className="text-sm text-brand-text-muted">{client.email}</p>
            </div>
            <div className="p-4 space-y-4">
                {/* User-Managed Tags Section */}
                <div>
                    <h4 className="text-sm font-semibold text-brand-text-muted flex items-center gap-2 mb-3"><Tag size={14} /> Your Tags</h4>
                    <div className="flex flex-wrap gap-2 items-center">
                        {(client.user_tags || []).map(tag => (
                            <span key={tag} className="flex items-center gap-1.5 bg-primary-action/20 text-brand-accent text-xs font-semibold pl-2.5 pr-1.5 py-1 rounded-full animate-in fade-in-0 zoom-in-95">
                                {tag}
                                <button onClick={() => handleRemoveTag(tag)} className="bg-black/10 hover:bg-black/30 rounded-full p-0.5 transition-colors"><X size={12} /></button>
                            </span>
                        ))}
                        <div className="flex-1 min-w-[120px]">
                            <input
                                type="text"
                                value={newTag}
                                onChange={(e) => setNewTag(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                                placeholder="Add tag..."
                                className="w-full bg-transparent text-sm text-brand-text-main placeholder:text-brand-text-muted/60 focus:outline-none"
                                disabled={isSaving}
                            />
                        </div>
                        <button onClick={handleAddTag} disabled={isSaving || !newTag.trim()} className="p-1.5 bg-white/10 text-brand-text-muted hover:text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                            <Plus size={14} />
                        </button>
                    </div>
                </div>

                {/* AI-Suggested Tags Section */}
                {(client.ai_tags || []).length > 0 && (
                    <div className="pt-2">
                        <h4 className="text-sm font-semibold text-brand-text-muted flex items-center gap-2 mb-3"><BrainCircuit size={14} /> AI Suggested Tags</h4>
                        <div className="flex flex-wrap gap-2">
                            {(client.ai_tags || []).map(tag => (
                                <span key={tag} className="bg-white/10 text-brand-text-muted text-xs font-semibold px-2.5 py-1 rounded-full">{tag}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};