// frontend/components/conversation/ChatHistory.tsx
// DEFINITIVE FIX: This component now only renders the list of messages.

'use client';

import React, { useRef, useEffect } from 'react';
import clsx from 'clsx';
import type { Client, Message } from '@/context/AppContext';
import { Avatar } from '../ui/Avatar';

interface ChatHistoryProps {
    messages: Message[];
    selectedClient: Client;
}

export const ChatHistory = ({ messages, selectedClient }: ChatHistoryProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }, [messages]);

    return (
        <div className="flex-grow overflow-y-auto">
            <div className="p-6 space-y-2 h-full">
                {messages.map(msg => (
                    <div key={msg.id} className={clsx("flex items-end gap-3", msg.direction === 'inbound' ? 'justify-start' : 'justify-end')}>
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
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};