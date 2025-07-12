// frontend/app/(main)/conversations/[clientId]/page.tsx
// --- DEFINITIVE FIX: Removes all frontend clearing logic to prevent race conditions.

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { find } from 'lodash';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import clsx from 'clsx';
import { useAppContext, Client, Message, ScheduledMessage } from '@/context/AppContext';
import { useSidebar } from '@/context/SidebarContext';

import { Tabs, TabOption } from '@/components/ui/Tabs';
import { DynamicTaggingCard } from '@/components/conversation/DynamicTaggingCard';
import { ClientIntelCard } from '@/components/conversation/ClientIntelCard';
import { RelationshipCampaignCard } from '@/components/conversation/RelationshipCampaignCard';
import { ChatHistory } from '@/components/conversation/ChatHistory';
import { MessageComposer } from '@/components/conversation/MessageComposer';
import { Avatar } from '@/components/ui/Avatar';
import { InfoCard } from '@/components/ui/InfoCard';
import { RecommendationActions } from '@/components/conversation/RecommendationActions';

import { Users, Menu, Phone, Video } from 'lucide-react';

interface ConversationPageProps {
    params: {
        clientId: string;
    };
}

interface ConversationData {
    messages: Message[];
    active_recommendations?: any;
}

interface MessageComposerHandle {
    setValue: (value: string) => void;
}

export default function ConversationPage({ params }: ConversationPageProps) {
    const { clientId } = params;
    const { loading, api, clients, properties, updateClientInList, refetchScheduledMessagesForClient } = useAppContext();
    const { setIsSidebarOpen } = useSidebar();
    
    const [error, setError] = useState<string | null>(null);
    const [selectedClient, setSelectedClient] = useState<Client | undefined>(undefined);
    const [conversationData, setConversationData] = useState<ConversationData | null>(null);
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [isSending, setIsSending] = useState(false);
    const [isPlanningCampaign, setIsPlanningCampaign] = useState(false);
    
    const [activeTab, setActiveTab] = useState<'messages' | 'intel'>('messages');
    const messageComposerRef = useRef<MessageComposerHandle>(null);

    const tabOptions: TabOption[] = [
        { id: 'messages', label: 'Messages' },
        { id: 'intel', label: 'Intel' }
    ];

    useEffect(() => {
        if (clients.length > 0) {
            const client = find(clients, { id: clientId });
            setSelectedClient(client);
        }
    }, [clientId, clients]);

    const fetchScheduled = useCallback(async (clientId: string) => {
        try {
            const scheduledData = await refetchScheduledMessagesForClient(clientId);
            setScheduledMessages(scheduledData);
        } catch (err: any) {
            console.error("Could not load scheduled messages:", err);
            setError(err.message || "Could not load scheduled messages.");
        }
    }, [refetchScheduledMessagesForClient]);
    
    useEffect(() => {
        if (!selectedClient) return;

        let isMounted = true;
        fetchScheduled(selectedClient.id);
        setActiveTab('messages');

        const pollForUpdates = async () => {
            if (!isMounted) return;
            try {
                const historyData: ConversationData = await api.get(`/api/messages/?client_id=${selectedClient.id}`);
        
                if (isMounted) {
                    // This simple update logic prevents the frontend from interfering with the backend.
                    setConversationData(prev => JSON.stringify(prev) !== JSON.stringify(historyData) ? historyData : prev);
                }
            } catch (err) {
                console.error("Polling failed:", err);
            }
        };

        pollForUpdates();
        const intervalId = setInterval(pollForUpdates, 5000);

        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [selectedClient, api, fetchScheduled]);

    const handleSendMessage = useCallback(async (content: string) => {
        if (!content.trim() || !selectedClient) return;
        setIsSending(true);

        const optimisticMessage: Message = { id: `agent-${Date.now()}`, client_id: selectedClient.id, content, direction: 'outbound', status: 'pending', created_at: new Date().toISOString() };
        setConversationData(prevData => {
            if (!prevData) return { messages: [optimisticMessage], active_recommendations: null };
            return {
                ...prevData,
                messages: [...prevData.messages, optimisticMessage]
            };
        });

        try {
            await api.post(`/api/conversations/${selectedClient.id}/send_reply`, { content });
            const historyData = await api.get(`/api/messages/?client_id=${selectedClient.id}`);
            setConversationData(historyData);
        } catch (err) {
            console.error("Failed to send message:", err);
            setConversationData(prev => prev ? { ...prev, messages: prev.messages.filter(m => m.id !== optimisticMessage.id) } : null);
            alert("Failed to send message.");
        } finally {
            setIsSending(false);
        }
    }, [selectedClient, api]);

    const handlePlanCampaign = useCallback(async () => {
    }, [selectedClient, api, refetchScheduledMessagesForClient]);

    const handleUpdateScheduledMessage = (updatedMessage: ScheduledMessage) => {
    };

    const handleActionComplete = useCallback((updatedClient: Client) => {
        console.log("Action complete, refreshing client data in the UI...");
        updateClientInList(updatedClient);
    }, [updateClientInList]);

    if (loading && !selectedClient) {
        return <div className="flex-1 flex items-center justify-center text-brand-text-muted">Loading Client Data...</div>;
    }
    if (error) {
        return <div className="flex-1 flex items-center justify-center text-red-400">Error: {error}</div>;
    }
    if (!selectedClient) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full text-brand-text-muted p-4">
                <Users className="w-16 h-16 mb-4" />
                <h1 className="text-xl font-medium text-center">Client not found</h1>
                <p className="text-center">The client with this ID could not be found. Please select a valid client from the list.</p>
            </div>
        );
    }
    
    return (
        <div className="flex-1 flex min-w-0">
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

                <div className="flex-shrink-0 p-2 border-b border-white/10 lg:hidden">
                    <Tabs
                        options={tabOptions}
                        activeTab={activeTab}
                        setActiveTab={(id) => setActiveTab(id as 'messages' | 'intel')}
                    />
                </div>

                <div className={clsx("flex flex-col flex-grow min-h-0", activeTab === 'messages' ? 'flex' : 'hidden lg:flex')}>
                   <ChatHistory 
                       conversationData={conversationData} 
                       selectedClient={selectedClient} 
                       onSendMessage={handleSendMessage}
                       messageComposerRef={messageComposerRef}
                   />
                   
                   {conversationData?.active_recommendations && selectedClient && (
                        <RecommendationActions
                            recommendations={conversationData.active_recommendations}
                            client={selectedClient}
                            onActionComplete={handleActionComplete}
                        />
                   )}

                   <MessageComposer onSendMessage={handleSendMessage} isSending={isSending} ref={messageComposerRef} />
                </div>

                <div className={clsx("p-6 space-y-6 overflow-y-auto", activeTab === 'intel' ? 'block lg:hidden' : 'hidden')}>
                    <DynamicTaggingCard client={selectedClient} onUpdate={updateClientInList} />
                    <ClientIntelCard client={selectedClient} onUpdate={updateClientInList} onReplan={handlePlanCampaign} />
                    <RelationshipCampaignCard messages={scheduledMessages} onReplan={handlePlanCampaign} onUpdateMessage={handleUpdateScheduledMessage} isPlanning={isPlanningCampaign} />
                </div>
            </main>

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