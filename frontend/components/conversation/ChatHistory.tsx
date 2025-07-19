// frontend/components/conversation/ChatHistory.tsx
// --- FINAL VERSION ---
// This version correctly renders all message source labels and inline recommendations.

'use client';

import React, { useRef, useEffect } from 'react';
import clsx from 'clsx';
import type { Client, Message, CampaignBriefing } from '@/context/AppContext';
import { Avatar } from '../ui/Avatar';
import { CoPilotBriefingCard } from './CoPilotBriefingCard';
import { AIDraftDisplay } from './AIDraftDisplay';
import { RecommendationActions } from './RecommendationActions';

// Ref type for the message composer handle
interface MessageComposerHandle {
    setValue: (value: string) => void;
}

interface ChatHistoryProps {
    messages: Message[];
    selectedClient: Client;
    recommendations: CampaignBriefing | null;
    onActionComplete: (updatedClient: Client) => void;
    onCoPilotActionSuccess: () => void;
    onSendMessage: (content: string) => Promise<void>;
    messageComposerRef: React.RefObject<MessageComposerHandle>;
}

export const ChatHistory = ({
    messages,
    selectedClient,
    recommendations,
    onActionComplete,
    onCoPilotActionSuccess,
    onSendMessage,
    messageComposerRef
}: ChatHistoryProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Scroll to the bottom smoothly when new messages or recommendations appear
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }, [messages, recommendations]);

    return (
        <div className="flex-grow overflow-y-auto">
            <div className="p-6 space-y-2 h-full">
                {messages.map((msg, index) => {
                    // Show recommendations for the most recent inbound message
                    const isLatestInboundMessage = msg.direction === 'inbound' && index === messages.length - 1;
                    const hasRecommendations = isLatestInboundMessage && recommendations;
                    const isCoPilotBriefing = hasRecommendations && recommendations?.campaign_type === 'co_pilot_briefing';
                    const isStandardRecommendation = hasRecommendations && !isCoPilotBriefing;

                    return (
                        <React.Fragment key={msg.id}>
                            {/* Render the message bubble */}
                            <div className={clsx("flex items-end gap-3", msg.direction === 'inbound' ? 'justify-start' : 'justify-end')}>
                                {msg.direction === 'inbound' && <Avatar name={selectedClient.full_name} className="w-8 h-8 text-xs" />}

                                <div className={clsx("p-3 px-4 rounded-t-xl max-w-lg", {
                                    'bg-gray-800 text-brand-text-muted rounded-br-xl': msg.direction === 'inbound',
                                    'bg-primary-action text-brand-dark font-medium rounded-bl-xl': msg.direction === 'outbound'
                                })}>
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                    {/* --- REVISED METADATA DISPLAY LOGIC --- */}
                                    <div className="flex items-center justify-end text-xs mt-1 opacity-70 gap-2">
                                        {msg.direction === 'outbound' && msg.source === 'instant_nudge' && (
                                            <span className="flex items-center gap-1 font-semibold text-cyan-400">
                                                ⚡️ <span className='opacity-80'>Instant Nudge</span>
                                            </span>
                                        )}
                                        {msg.direction === 'outbound' && msg.source === 'scheduled' && (
                                            <span className="flex items-center gap-1 font-semibold">
                                                🕒 <span className='opacity-80'>Scheduled</span>
                                            </span>
                                        )}
                                        {msg.direction === 'outbound' && msg.source === 'faq_auto_response' && (
                                            <span className="flex items-center gap-1 font-semibold">
                                                ✨ <span className='opacity-80'>Auto-Response</span>
                                            </span>
                                        )}
                                        <span>
                                            {msg.source === 'scheduled' && msg.originally_scheduled_at 
                                                ? new Date(msg.originally_scheduled_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
                                                : new Date(msg.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
                                            }
                                        </span>
                                    </div>
                                    {/* --- END REVISED LOGIC --- */}
                                </div>
                            </div>
                            
                            {/* Render recommendations for the latest inbound message */}
                            {isCoPilotBriefing && recommendations && (
                                <div className="mt-2 ml-11 max-w-lg">
                                    <CoPilotBriefingCard 
                                        briefing={recommendations} 
                                        onActionSuccess={onCoPilotActionSuccess} 
                                    />
                                </div>
                            )}

                            {isStandardRecommendation && recommendations && (
                                <div className="mt-2 ml-11 max-w-lg space-y-2">
                                     {recommendations.original_draft && (
                                        <AIDraftDisplay
                                            draft={recommendations}
                                            onSendMessage={onSendMessage}
                                            messageComposerRef={messageComposerRef}
                                        />
                                    )}
                                    <RecommendationActions
                                        recommendations={recommendations}
                                        client={selectedClient}
                                        onActionComplete={onActionComplete}
                                    />
                                </div>
                            )}
                        </React.Fragment>
                    );
                })}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};