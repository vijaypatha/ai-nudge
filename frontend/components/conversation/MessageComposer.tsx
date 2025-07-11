// frontend/components/conversation/MessageComposer.tsx
// Purpose: Renders the text input and send button for composing messages.
// MODIFIED: Added React.forwardRef and useImperativeHandle to expose a setValue function.

'use client';

import { useState, useRef, useImperativeHandle, forwardRef } from 'react'; // Import forwardRef and useImperativeHandle
import { Paperclip, Send } from 'lucide-react';

/**
 * Props for the MessageComposer.
 * @param onSendMessage - Callback to handle sending the message.
 * @param isSending - Boolean to disable the composer while a message is in flight.
 */
interface MessageComposerProps {
    onSendMessage: (content: string) => Promise<void>;
    isSending: boolean;
}

/**
 * A controlled component for the message input field and send controls.
 * Uses forwardRef to allow parent components to imperatively set the input value.
 */
export const MessageComposer = forwardRef<
    { setValue: (value: string) => void }, // The type of the ref handle
    MessageComposerProps // The props of the component
>(({ onSendMessage, isSending }, ref) => { // Receive ref as the second argument
    const [content, setContent] = useState('');

    // Expose a setValue function to the parent component via the ref
    useImperativeHandle(ref, () => ({
        setValue: (value: string) => {
            setContent(value);
        },
    }));

    const handleSend = async () => {
        if (!content.trim() || isSending) return;
        // The parent component will handle the API call and optimistic update.
        await onSendMessage(content);
        // Clear input on successful send.
        setContent('');
    };

    return (
        <div className="p-4 bg-black/10 border-t border-white/10 flex-shrink-0">
            <div className="relative bg-white/5 border border-white/10 rounded-xl flex items-center">
                <input
                    type="text"
                    placeholder="Type your message..."
                    className="flex-grow bg-transparent text-brand-text-main placeholder-brand-text-muted/60 focus:outline-none pl-4"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !isSending) handleSend(); }}
                    disabled={isSending}
                />
                <button className="p-3 text-brand-text-muted hover:text-brand-accent">
                    <Paperclip className="w-5 h-5" />
                </button>
                <button
                    className="bg-primary-action hover:brightness-110 text-brand-dark p-3 rounded-r-xl m-0.5 disabled:opacity-50"
                    onClick={handleSend}
                    disabled={!content.trim() || isSending}
                >
                    <Send className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
});

// Add a display name for better debugging in React DevTools
MessageComposer.displayName = 'MessageComposer';
