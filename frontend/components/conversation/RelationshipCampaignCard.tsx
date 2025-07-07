// frontend/components/conversation/RelationshipCampaignCard.tsx
// Purpose: A card to display and manage the scheduled messages for a client's relationship campaign.

'use client';

import { useState } from 'react';
import { Zap, Gift, Star, Sparkles, Calendar, Edit2, Loader2 } from 'lucide-react';
import { useAppContext, ScheduledMessage } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { EditMessageModal } from './EditMessageModal';

/**
 * Props for the RelationshipCampaignCard.
 * @param messages - An array of scheduled messages for the client.
 * @param onReplan - Callback to trigger a new campaign plan.
 * @param onUpdateMessage - Callback to update a message in the list after editing.
 * @param isPlanning - Boolean to indicate if a planning operation is in progress.
 */
interface RelationshipCampaignCardProps {
    messages: ScheduledMessage[];
    onReplan: () => void;
    onUpdateMessage: (updatedMessage: ScheduledMessage) => void;
    isPlanning: boolean;
}

/**
 * Renders a card listing scheduled campaign messages, allowing for edits and replanning.
 */
export const RelationshipCampaignCard = ({ messages, onReplan, onUpdateMessage, isPlanning }: RelationshipCampaignCardProps) => {
    const { api } = useAppContext();
    const [editingMessage, setEditingMessage] = useState<ScheduledMessage | null>(null);

    // Determines the appropriate icon based on the message content.
    const getIconForMessage = (content: string) => {
        const lowerContent = content.toLowerCase();
        if (lowerContent.includes('birthday')) return <Gift size={16} className="text-brand-accent" />;
        if (lowerContent.includes('check-in')) return <Star size={16} className="text-brand-accent" />;
        if (lowerContent.includes('holiday')) return <Sparkles size={16} className="text-brand-accent" />;
        return <Calendar size={16} className="text-brand-accent" />;
    };

    return (
        <>
            {/* The modal is rendered here but only visible when `editingMessage` is not null */}
            <EditMessageModal
                api={api}
                isOpen={!!editingMessage}
                onClose={() => setEditingMessage(null)}
                message={editingMessage}
                onSave={onUpdateMessage}
            />
            <InfoCard title="Relationship Campaign" icon={<Zap size={14} />}>
                {messages.length > 0 ? (
                    <ul className="space-y-1 pt-2">
                        {messages.map(msg => (
                            <li
                                key={msg.id}
                                onClick={() => setEditingMessage(msg)}
                                className="group flex items-center justify-between hover:bg-white/5 -mx-2 px-2 py-2 rounded-md cursor-pointer transition-all"
                            >
                                <div className="flex items-start gap-4">
                                    <div className="mt-1 flex-shrink-0">{getIconForMessage(msg.content)}</div>
                                    <div>
                                        <p className="font-semibold text-sm text-brand-text-main">
                                            {new Date(msg.scheduled_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}
                                        </p>
                                        <p className="text-xs text-brand-text-muted break-words whitespace-pre-wrap">{msg.content.split('\n')[0]}</p>
                                    </div>
                                </div>
                                <div className="opacity-0 group-hover:opacity-100 transition-opacity pr-1">
                                    <Edit2 size={14} className="text-brand-text-muted" />
                                </div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <div className="text-center py-4">
                        <p className="text-sm text-brand-text-muted mb-3">No campaign planned for this client.</p>
                        <button
                            onClick={onReplan}
                            disabled={isPlanning}
                            className="w-full px-3 py-2 text-sm font-semibold bg-primary-action/20 text-brand-accent hover:bg-primary-action/30 rounded-md disabled:opacity-50 disabled:cursor-wait flex items-center justify-center gap-2"
                        >
                            {isPlanning ? (
                                <><Loader2 size={16} className="animate-spin" /> Planning...</>
                            ) : (
                                `+ Plan Relationship Campaign`
                            )}
                        </button>
                    </div>
                )}
            </InfoCard>
        </>
    );
};