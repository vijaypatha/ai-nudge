// frontend/context/AppContext.tsx
'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

// --- SHARED TYPE SCRIPT INTERFACES ---
export interface Client { id: string; full_name: string; email: string; phone?: string; tags: string[]; preferences: any; }
export interface Property { id: string; address: string; price: number; status: string; image_urls: string[]; }
export interface Message { id: string; sender: 'client' | 'agent' | 'ai'; content: string; timestamp: string; is_ai_draft?: boolean; }
export interface Conversation {
  id: string;
  client_id: string;
  client_name: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
  messages: Message[];
}
export interface ScheduledMessage { id: string; content: string; scheduled_at: string; status: string; }
export interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reason: string; }
export interface CampaignBriefing {
  id: string; user_id: string; client_id: string; campaign_type: string; headline: string;
  listing_url?: string; key_intel: { [key: string]: string }; original_draft: string;
  edited_draft?: string; matched_audience: MatchedClient[]; status: 'new' | 'launched' | 'dismissed';
}


// Define the shape of our global context
interface AppContextType {
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  clients: Client[];
  setClients: React.Dispatch<React.SetStateAction<Client[]>>;
  conversations: Conversation[];
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>;
}

// Create the context
const AppContext = createContext<AppContextType | undefined>(undefined);

// Create the Provider component that will wrap our application
export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [clients, setClients] = useState<Client[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const value = { loading, setLoading, clients, setClients, conversations, setConversations };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

// Create a custom hook for easy access to our global state
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};