// frontend/components/conversation/ChatHistory.tsx
// --- FINAL CLEANED VERSION ---

'use client';

import React, { useRef, useEffect } from 'react';
import clsx from 'clsx';
import type { Client } from '@/context/AppContext';
import { Avatar } from '../ui/Avatar';
import { AIDraftDisplay } from './AIDraftDisplay';

// Define the shape of a single message
interface Message {
  id: string;
  content: string;
  direction: 'inbound' | 'outbound';
  created_at: string;
  ai_draft?: any;
}

// Define the shape of the conversation data object
interface ConversationData {
    messages: Message[];
    active_recommendations?: any;
}

interface MessageComposerHandle {
    setValue: (value: string) => void;
}

interface ChatHistoryProps {
    // --- MODIFIED: The component now expects a single 'conversationData' prop ---
    conversationData: ConversationData | null;
    selectedClient: Client;
    onSendMessage: (content: string) => Promise<void>;
    messageComposerRef: React.RefObject<MessageComposerHandle>;
}

export const ChatHistory = ({ conversationData, selectedClient, onSendMessage, messageComposerRef }: ChatHistoryProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Extract the messages array from the conversationData object.
    // Provide a default empty array to prevent crashes if data is loading or null.
    const messages = conversationData?.messages || [];

    useEffect(() => {
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }, [messages]);

    return (
        <div className="flex-grow overflow-y-auto">
            <div className="p-6 space-y-2 h-full">
                {/* The .map() function now safely operates on the extracted messages array */}
                {messages.map(msg => (
                    <div key={msg.id} className="flex flex-col">
                        <div className={clsx("flex items-end gap-3", msg.direction === 'inbound' ? 'justify-start' : 'justify-end')}>
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
                        
                        {msg.direction === 'inbound' && msg.ai_draft && (
                            <AIDraftDisplay
                                draft={msg.ai_draft}
                                onSendMessage={onSendMessage}
                                messageComposerRef={messageComposerRef}
                            />
                        )}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};