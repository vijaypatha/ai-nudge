// File Path: frontend/app/(main)/conversations/page.tsx
// Purpose: This is the default view for the conversations section.
// It displays a prompt to select a conversation from the sidebar.

'use client';

import { MessageSquare } from 'lucide-react';

export default function SelectConversationPage() {
  return (
    <div className="flex flex-col h-full items-center justify-center text-brand-text-muted p-4">
      <MessageSquare className="w-16 h-16 mb-4" />
      <h1 className="text-xl font-medium text-center">Select a conversation</h1>
      <p className="text-center">Choose a client from the list to start messaging.</p>
    </div>
  );
}