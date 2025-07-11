// frontend/components/conversation/ChatHistory.tsx
// Purpose: Renders the scrollable list of messages in a conversation.
// --- MODIFIED: Now renders an inline AI draft component beneath its parent message.

'use client';

import React, { useRef, useEffect } from 'react';
import clsx from 'clsx';
import type { Message, Client } from '@/context/AppContext';
import { Avatar } from '../ui/Avatar';
// --- ADDED: Import the new AIDraftDisplay component ---
import { AIDraftDisplay } from './AIDraftDisplay';

// --- ADDED: Ref type for the message composer ---
interface MessageComposerHandle {
    setValue: (value: string) => void;
}

/**
 * --- MODIFIED: Props for the ChatHistory component now include handlers ---
 * @param messages - An array of messages to display.
 * @param selectedClient - The client participating in the conversation.
 * @param onSendMessage - Callback function to send a message.
 * @param messageComposerRef - Ref to the MessageComposer for editing.
 */
interface ChatHistoryProps {
    messages: Message[];
    selectedClient: Client;
    onSendMessage: (content: string) => Promise<void>;
    messageComposerRef: React.RefObject<MessageComposerHandle>;
}

/**
 * Displays a list of chat messages and auto-scrolls to the bottom.
 */
export const ChatHistory = ({ messages, selectedClient, onSendMessage, messageComposerRef }: ChatHistoryProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Effect to scroll to the latest message whenever the messages array changes.
    useEffect(() => {
        // A slight delay can help ensure the DOM has updated before scrolling
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }, [messages]);

    return (
        <div className="flex-grow overflow-y-auto">
            <div className="p-6 space-y-2 h-full"> {/* Reduced space-y for tighter grouping */}
                {messages.map(msg => (
                    <div key={msg.id} className="flex flex-col">
                        {/* Message Bubble */}
                        <div className={clsx("flex items-end gap-3", msg.direction === 'inbound' ? 'justify-start' : 'justify-end')}>
                            {/* Show avatar only for inbound messages */}
                            {msg.direction === 'inbound' && <Avatar name={selectedClient.full_name} className="w-8 h-8 text-xs" />}

                            <div className={clsx("p-3 px-4 rounded-t-xl max-w-lg", {
                                'bg-gray-800 text-brand-text-muted rounded-br-xl': msg.direction === 'inbound',
                                'bg-primary-action text-brand-dark font-medium rounded-bl-xl': msg.direction === 'outbound'
                            })}>
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                                <p className="text-right text-xs mt-1 opacity-70">
                                    {new Date(msg.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                                </p>
                            </div>
                        </div>

                        {/* --- ADDED: Inline AI Draft Component --- */}
                        {/* If the message is inbound and has an associated draft, display it here. */}
                        {msg.direction === 'inbound' && msg.ai_draft && (
                            <AIDraftDisplay
                                draft={msg.ai_draft}
                                onSendMessage={onSendMessage}
                                messageComposerRef={messageComposerRef}
                            />
                        )}
                    </div>
                ))}
                {/* Empty div to act as a scroll target */}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};