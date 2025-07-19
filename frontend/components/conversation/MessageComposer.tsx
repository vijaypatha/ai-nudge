// frontend/components/conversation/MessageComposer.tsx
// Purpose: Renders the text input and send button for composing messages.
// MODIFIED: Added React.forwardRef and useImperativeHandle to expose a setValue function.

'use client';

import { useState, useRef, useImperativeHandle, forwardRef } from 'react'; // Import forwardRef and useImperativeHandle
import { Paperclip, Send, CalendarClock } from 'lucide-react';

interface MessageComposerProps {
    onSendMessage: (content: string) => void;
    onOpenScheduleModal: (content: string) => void; // Changed prop
    isSending: boolean;
}

/**
 * Props for the MessageComposer.
 * @param onSendMessage - Callback to handle sending the message.
 * @param isSending - Boolean to disable the composer while a message is in flight.
 */
interface MessageComposerProps {
    onSendMessage: (content: string) => void;
    onScheduleMessage: (content: string, scheduledAt: string) => void;
    isSending: boolean;
}

export const MessageComposer = forwardRef<
    { setValue: (value: string) => void },
    MessageComposerProps
>(({ onSendMessage, onOpenScheduleModal, isSending }, ref) => {
    const [content, setContent] = useState('');

    useImperativeHandle(ref, () => ({
        setValue: (value: string) => {
            setContent(value);
        },
    }));

    const handleSend = async () => {
        if (!content.trim() || isSending) return;
        await onSendMessage(content);
        setContent('');
    };

    const handleScheduleClick = () => {
        onOpenScheduleModal(content);
    };

    return (
        <div className="p-4 bg-black/10 border-t border-white/10 flex-shrink-0">
            <div className="relative bg-white/5 border border-white/10 rounded-xl flex items-center pr-1.5">
                <input
                    type="text"
                    placeholder="Type your message..."
                    className="flex-grow bg-transparent text-brand-text-main placeholder-brand-text-muted/60 focus:outline-none pl-4 py-3"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !isSending) handleSend(); }}
                    disabled={isSending}
                />
                <div className="flex items-center gap-1">
                    <button 
                        onClick={handleScheduleClick}
                        className="p-2.5 text-brand-text-muted hover:text-brand-accent rounded-lg hover:bg-white/5"
                        title="Schedule Message"
                    >
                        <CalendarClock className="w-5 h-5" />
                    </button>
                    <button
                        className="bg-primary-action hover:brightness-110 text-brand-dark p-2.5 rounded-lg disabled:opacity-50"
                        onClick={handleSend}
                        disabled={!content.trim() || isSending}
                        title="Send Message"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
});

MessageComposer.displayName = 'MessageComposer';

// Add a display name for better debugging in React DevTools
MessageComposer.displayName = 'MessageComposer';
