// frontend/components/conversation/ChatHistory.tsx
// Purpose: Renders the scrollable list of messages in a conversation.

'use client';

import { useRef, useEffect } from 'react';
import clsx from 'clsx';
import type { Message, Client } from '@/context/AppContext';
import { Avatar } from '../ui/Avatar';

/**
 * Props for the ChatHistory component.
 * @param messages - An array of messages to display.
 * @param selectedClient - The client participating in the conversation.
 */
interface ChatHistoryProps {
    messages: Message[];
    selectedClient: Client;
}

/**
 * Displays a list of chat messages and auto-scrolls to the bottom.
 */
export const ChatHistory = ({ messages, selectedClient }: ChatHistoryProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Effect to scroll to the latest message whenever the messages array changes.
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (
        <div className="flex-grow overflow-y-auto">
            <div className="p-6 space-y-6 h-full">
                {messages.map(msg => (
                    <div key={msg.id} className={clsx("flex items-end gap-3", msg.direction === 'inbound' ? 'justify-start' : 'justify-end')}>
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
                ))}
                {/* Empty div to act as a scroll target */}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};