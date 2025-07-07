// frontend/app/(main)/conversations/[clientId]/page.tsx
// Purpose: The dedicated "Conversation Workspace" for a single client. It fetches
// and manages all state related to a specific conversation, including chat history,
// composer state, and client-specific intel.

'use client';

import { useState, useEffect, useCallback } from 'react';
import { find } from 'lodash';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import clsx from 'clsx';
import { useAppContext, Client, Message, ScheduledMessage } from '@/context/AppContext';
import { useSidebar } from '@/context/SidebarContext';

// Import the extracted components
import { DynamicTaggingCard } from '@/components/conversation/DynamicTaggingCard';
import { ClientIntelCard } from '@/components/conversation/ClientIntelCard';
import { RelationshipCampaignCard } from '@/components/conversation/RelationshipCampaignCard';
import { ChatHistory } from '@/components/conversation/ChatHistory';
import { MessageComposer } from '@/components/conversation/MessageComposer';
import { Avatar } from '@/components/ui/Avatar';
import { InfoCard } from '@/components/ui/InfoCard';

// Import icons
import { Users, Menu, Phone, Video } from 'lucide-react';

// Define props for the page, including params from the dynamic route.
interface ConversationPageProps {
    params: {
        clientId: string;
    };
}

/**
 * This is the main component for the conversation view.
 * It fetches and manages the state for a single conversation.
 */
export default function ConversationPage({ params }: ConversationPageProps) {
    const { clientId } = params;
    const { loading, api, clients, properties, updateClientInList, refetchScheduledMessagesForClient } = useAppContext();
    const { setIsSidebarOpen } = useSidebar(); // Get sidebar control from context
    const router = useRouter();

    // State for this specific page
    const [error, setError] = useState<string | null>(null);
    const [selectedClient, setSelectedClient] = useState<Client | undefined>(undefined);
    const [currentMessages, setCurrentMessages] = useState<Message[]>([]);
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [isSending, setIsSending] = useState(false);
    const [isPlanningCampaign, setIsPlanningCampaign] = useState(false);
    const [activeTab, setActiveTab] = useState<'messages' | 'intel'>('messages'); // For mobile responsive tabs

    // Effect to find the full client object from the list when the clientId changes.
    useEffect(() => {
        if (clients.length > 0) {
            const client = find(clients, { id: clientId });
            setSelectedClient(client);
        }
    }, [clientId, clients]);

    // Effect to fetch conversation details when a client is selected.
    useEffect(() => {
        if (!selectedClient) return;

        const fetchConversationDetails = async () => {
            console.log(`Fetching details for client: ${selectedClient.id}`);
            setError(null); // Clear previous errors
            try {
                // --- BUGFIX: The API endpoint for message history is /api/messages/, not /api/conversations/[id] ---
                // It uses a query parameter `client_id` as defined in the backend `conversations.py` file.
                const historyPromise = api.get(`/api/messages/?client_id=${selectedClient.id}`);
                const scheduledPromise = refetchScheduledMessagesForClient(selectedClient.id);
                
                const [historyData, scheduledData] = await Promise.all([historyPromise, scheduledPromise]);

                setCurrentMessages(historyData);
                setScheduledMessages(scheduledData);
                console.log(`Successfully fetched details for client: ${selectedClient.id}`);
            } catch (err: any) {
                console.error("Could not load conversation details:", err);
                setError(err.message || "Could not load conversation details.");
            }
        };

        fetchConversationDetails();
        setActiveTab('messages'); // Default to messages tab on new client select
    }, [selectedClient, api, refetchScheduledMessagesForClient]);

    // Callback for the MessageComposer to send a message.
    const handleSendMessage = useCallback(async (content: string) => {
        if (!content.trim() || !selectedClient) return;

        console.log(`Sending message to client: ${selectedClient.id}`);
        setIsSending(true);

        const optimisticMessage: Message = {
            id: `agent-${Date.now()}`,
            client_id: selectedClient.id,
            content: content,
            direction: 'outbound',
            status: 'pending',
            created_at: new Date().toISOString()
        };
        setCurrentMessages(prev => [...prev, optimisticMessage]);

        try {
            await api.post(`/conversations/${selectedClient.id}/send_reply`, { content });
            // After sending, refetch the history to get the confirmed message
            const historyData = await api.get(`/api/messages/?client_id=${selectedClient.id}`);
            setCurrentMessages(historyData);
        } catch (err) {
            console.error("Failed to send message:", err);
            // If the API call fails, remove the optimistic message
            setCurrentMessages(prev => prev.filter(m => m.id !== optimisticMessage.id));
            alert("Failed to send message.");
        } finally {
            setIsSending(false);
        }
    }, [selectedClient, api]);

    // Callback to trigger campaign planning.
    const handlePlanCampaign = useCallback(async () => {
        if (!selectedClient) return;
        
        console.log(`Planning campaign for client: ${selectedClient.id}`);
        setIsPlanningCampaign(true);
        try {
            await api.post(`/campaigns/plan-relationship`, { client_id: selectedClient.id });
            const updatedMessages = await refetchScheduledMessagesForClient(selectedClient.id);
            setScheduledMessages(updatedMessages);
            console.log(`Campaign planned successfully for client: ${selectedClient.id}`);
        } catch (err) {
            console.error("Failed to plan campaign:", err);
            alert("There was an error planning the campaign.");
        } finally {
            setIsPlanningCampaign(false);
        }
    }, [selectedClient, api, refetchScheduledMessagesForClient]);

    // Callback to update a scheduled message in the local state after editing.
    const handleUpdateScheduledMessage = (updatedMessage: ScheduledMessage) => {
        setScheduledMessages(prev => prev.map(msg => msg.id === updatedMessage.id ? updatedMessage : msg));
    };

    // --- RENDER LOGIC ---

    // Loading state while the initial client data is being fetched by the context
    if (loading && !selectedClient) {
        return <div className="flex-1 flex items-center justify-center text-brand-text-muted">Loading Client Data...</div>;
    }

    // Error state if fetching conversation details fails
    if (error) {
        return <div className="flex-1 flex items-center justify-center text-red-400">Error: {error}</div>;
    }

    // State when the client ID is invalid or not found in the main client list
    if (!selectedClient) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full text-brand-text-muted p-4">
                <Users className="w-16 h-16 mb-4" />
                <h1 className="text-xl font-medium text-center">Client not found</h1>
                <p className="text-center">The client with this ID could not be found. Please select a valid client from the list.</p>
            </div>
        );
    }
    
    // Main three-column layout render
    return (
        <div className="flex-1 flex min-w-0">
            {/* Center Column: Chat View */}
            <main className="flex-1 flex flex-col min-w-0 lg:border-l lg:border-r border-white/10">
                <header className="flex items-center justify-between p-4 border-b border-white/10 bg-brand-dark/50 backdrop-blur-sm sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <button onClick={() => setIsSidebarOpen(true)} className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden">
                            <Menu className="w-6 h-6" />
                        </button>
                        <Avatar name={selectedClient.full_name} className="w-11 h-11 hidden sm:flex" />
                        <div>
                            <h2 className="text-xl font-bold text-brand-text-main">{selectedClient.full_name}</h2>
                            <p className="text-sm text-brand-accent">Online</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 hover:text-brand-text-main"><Phone className="w-5 h-5" /></button>
                        <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 hover:text-brand-text-main"><Video className="w-5 h-5" /></button>
                    </div>
                </header>

                {/* Tab switcher for mobile */}
                <div className="flex-shrink-0 border-b border-white/10 lg:hidden">
                    <nav className="flex">
                        <button onClick={() => setActiveTab('messages')} className={clsx("flex-1 p-3 text-sm font-semibold text-center", activeTab === 'messages' ? 'text-brand-accent border-b-2 border-brand-accent' : 'text-brand-text-muted')}>Messages</button>
                        <button onClick={() => setActiveTab('intel')} className={clsx("flex-1 p-3 text-sm font-semibold text-center", activeTab === 'intel' ? 'text-brand-accent border-b-2 border-brand-accent' : 'text-brand-text-muted')}>Intel</button>
                    </nav>
                </div>

                {/* Main Content: Chat or Intel view, conditionally rendered for mobile */}
                <div className={clsx("flex flex-col flex-grow min-h-0", activeTab === 'messages' ? 'flex' : 'hidden lg:flex')}>
                   <ChatHistory messages={currentMessages} selectedClient={selectedClient} />
                   <MessageComposer onSendMessage={handleSendMessage} isSending={isSending} />
                </div>

                <div className={clsx("p-6 space-y-6 overflow-y-auto", activeTab === 'intel' ? 'block lg:hidden' : 'hidden')}>
                    <DynamicTaggingCard client={selectedClient} onUpdate={updateClientInList} />
                    <ClientIntelCard client={selectedClient} onUpdate={updateClientInList} onReplan={handlePlanCampaign} />
                    <RelationshipCampaignCard messages={scheduledMessages} onReplan={handlePlanCampaign} onUpdateMessage={handleUpdateScheduledMessage} isPlanning={isPlanningCampaign} />
                </div>
            </main>

            {/* Right Column: Intel View (desktop) */}
            <aside className="bg-white/5 p-6 flex-col gap-6 overflow-y-auto w-96 flex-shrink-0 hidden lg:flex">
                <DynamicTaggingCard client={selectedClient} onUpdate={updateClientInList} />
                <ClientIntelCard client={selectedClient} onUpdate={updateClientInList} onReplan={handlePlanCampaign} />
                <RelationshipCampaignCard messages={scheduledMessages} onReplan={handlePlanCampaign} onUpdateMessage={handleUpdateScheduledMessage} isPlanning={isPlanningCampaign} />
                <InfoCard title="Properties">
                    <ul className="space-y-4">
                        {properties.slice(0, 3).map(property => (
                            <li key={property.id} className="flex items-center gap-4">
                                <div className="relative w-20 h-16 bg-brand-dark rounded-md overflow-hidden flex-shrink-0">
                                    <Image src={property.image_urls?.[0] || `https://placehold.co/300x200/0B112B/C4C4C4?text=${property.address.split(',')[0]}`} alt={`Image of ${property.address}`} layout="fill" objectFit="cover" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-brand-text-main truncate">{property.address}</h4>
                                    <p className="text-sm text-brand-text-muted">${property.price.toLocaleString()}</p>
                                    <p className="text-xs text-brand-accent font-medium">{property.status}</p>
                                </div>
                            </li>
                        ))}
                    </ul>
                </InfoCard>
            </aside>
        </div>
    );
}
