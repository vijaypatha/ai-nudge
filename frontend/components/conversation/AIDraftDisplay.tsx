// frontend/components/conversation/AIDraftDisplay.tsx
// --- NEW FILE ---
// Purpose: Renders the inline AI draft with Edit and Send controls.

'use client';

import React from 'react';
import type { CampaignBriefing } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { Edit, Send } from 'lucide-react';

// Ref type for the message composer handle
interface MessageComposerHandle {
    setValue: (value: string) => void;
}

interface AIDraftDisplayProps {
    draft: CampaignBriefing;
    onSendMessage: (content: string) => Promise<void>;
    messageComposerRef: React.RefObject<MessageComposerHandle>;
}

export const AIDraftDisplay = ({ draft, onSendMessage, messageComposerRef }: AIDraftDisplayProps) => {
    
    /**
     * Handles the "Edit" button click.
     * It populates the main message composer with the draft's text.
     */
    const handleEdit = () => {
        if (messageComposerRef.current) {
            messageComposerRef.current.setValue(draft.original_draft);
        }
    };

    /**
     * Handles the "Send" button click.
     * It uses the parent's onSendMessage function to send the draft text.
     */
    const handleSend = async () => {
        await onSendMessage(draft.original_draft);
    };

    return (
        // This container aligns the draft below the incoming message bubble
        <div className="mt-2 ml-11 max-w-lg">
            <div className="bg-brand-dark-blue/80 rounded-lg p-3 shadow-lg border border-primary-action/30">
                <h3 className="text-brand-text-main font-semibold mb-2 text-sm">
                    <span className="text-brand-accent">AI Draft:</span>
                </h3>
                <p className="text-brand-text-muted mb-4 text-sm leading-relaxed">{draft.original_draft}</p>
                <div className="flex gap-2 justify-end">
                    <Button variant="secondary" onClick={handleEdit} size="sm" className="flex items-center gap-1">
                        <Edit className="w-4 h-4" /> Edit
                    </Button>
                    <Button onClick={handleSend} size="sm" className="flex items-center gap-1">
                        <Send className="w-4 h-4" /> Send
                    </Button>
                </div>
            </div>
        </div>
    );
};