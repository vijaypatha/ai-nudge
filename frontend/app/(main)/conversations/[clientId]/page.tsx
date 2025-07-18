// frontend/app/(main)/conversations/[clientId]/page.tsx
// --- FINAL, ROBUST VERSION (LAYOUT FIX) ---
// This version refactors the JSX to correctly implement a two-column layout
// on desktop (Chat + Intel Sidebar) and a tabbed view on mobile.

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import clsx from 'clsx';
import { useAppContext, Client, Message, ScheduledMessage, CampaignBriefing } from '@/context/AppContext';
import { useSidebar } from '@/context/SidebarContext';

import { Tabs, TabOption } from '@/components/ui/Tabs';
import { DynamicTaggingCard } from '@/components/conversation/DynamicTaggingCard';
import { ClientIntelCard } from '@/components/conversation/ClientIntelCard';
import { RelationshipCampaignCard } from '@/components/conversation/RelationshipCampaignCard';
import { ChatHistory } from '@/components/conversation/ChatHistory';
import { MessageComposer } from '@/components/conversation/MessageComposer';
import { Avatar } from '@/components/ui/Avatar';
import { InfoCard } from '@/components/ui/InfoCard';
import { Users, Menu, Phone, Video, Loader2 } from 'lucide-react';
const POLLING_INTERVAL = 5000; // Poll every 5 seconds

export interface ConversationDisplayConfig {
    client_intel: { title: string; icon: string; };
    relationship_campaign: { title: string; icon: string; };
    properties: { title: string; icon: string; };
}

interface ConversationPageProps {
    params: {
        clientId: string;
    };
}

interface ConversationData {
    messages: Message[];
    immediate_recommendations: CampaignBriefing | null;
    active_plan: CampaignBriefing | null;
    display_config: ConversationDisplayConfig;
}

interface MessageComposerHandle {
    setValue: (value: string) => void;
}

export default function ConversationPage({ params }: ConversationPageProps) {
    const { clientId } = params;
    const { api, properties, updateClientInList, refetchScheduledMessagesForClient, refreshConversations } = useAppContext();
    const { setIsSidebarOpen } = useSidebar();
    const router = useRouter();
    
    const [pageState, setPageState] = useState<'loading' | 'error' | 'loaded'>('loading');
    const [selectedClient, setSelectedClient] = useState<Client | null>(null);
    const [conversationData, setConversationData] = useState<Omit<ConversationData, 'display_config'> | null>(null);
    const [displayConfig, setDisplayConfig] = useState<ConversationDisplayConfig | null>(null);
    const ws = useRef<WebSocket | null>(null);
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [isSending, setIsSending] = useState(false);
    const [isPlanProcessing, setIsPlanProcessing] = useState(false);
    const [isPlanSuccess, setIsPlanSuccess] = useState(false);
    
    const [activeTab, setActiveTab] = useState<'messages' | 'intel'>('messages');
    const messageComposerRef = useRef<MessageComposerHandle>(null);

    const tabOptions: TabOption[] = [
        { id: 'messages', label: 'Messages' },
        { id: 'intel', label: 'Intel' }
    ];

    const fetchConversationData = useCallback(async (currentClientId: string) => {
        if (!api) return;
        try {
            const [convoData, scheduledData] = await Promise.all([
                api.get(`/api/messages/?client_id=${currentClientId}`),
                refetchScheduledMessagesForClient(currentClientId)
            ]);

            const newConvoState = {
                messages: convoData.messages,
                immediate_recommendations: convoData.immediate_recommendations,
                active_plan: convoData.active_plan,
            };

            // Use functional updates with deep comparison to prevent unnecessary re-renders
            setConversationData(prevState => 
                JSON.stringify(prevState) === JSON.stringify(newConvoState) ? prevState : newConvoState
            );
            setDisplayConfig(prevState => 
                JSON.stringify(prevState) === JSON.stringify(convoData.display_config) ? prevState : convoData.display_config
            );
            setScheduledMessages(prevState =>
                JSON.stringify(prevState) === JSON.stringify(scheduledData) ? prevState : scheduledData
            );

        } catch (error) {
            console.error("Polling failed for conversation data:", error);
            // Do not reset state on a transient polling error, which could cause a flicker.
        }
    }, [api, refetchScheduledMessagesForClient]);

    useEffect(() => {
        const fetchClientAndConversation = async () => {
            if (!clientId || !api) return;
            setPageState('loading');
            try {
                const clientData = await api.get(`/api/clients/${clientId}`);
                setSelectedClient(clientData);
                await fetchConversationData(clientId);
                setPageState('loaded');
            } catch (error) {
                console.error("Failed to fetch client:", error);
                setPageState('error');
            }
        };
        fetchClientAndConversation();
    }, [clientId, api, fetchConversationData]);

// This version uses a ref to hold callback handlers, ensuring the connection
// is stable and does not reset on re-renders.
const handlersRef = useRef({ fetchConversationData, refreshConversations });

useEffect(() => {
    handlersRef.current = { fetchConversationData, refreshConversations };
}, [fetchConversationData, refreshConversations]);

useEffect(() => {
    if (!clientId) return;

    const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBaseUrl}/api/ws/${clientId}`;



    console.log(`WS: Attempting to connect to ${wsUrl}`);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => console.log(`WS: Connection established for client ${clientId}`);

    ws.current.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('WS: Message received:', data);
            if (data.type === 'NEW_MESSAGE' && data.clientId === clientId) {
                console.log('WS: New message notification received. Refetching data...');
                // Call the handlers through the stable ref
                handlersRef.current.fetchConversationData(clientId);
                handlersRef.current.refreshConversations();
            }
        } catch (e) {
            console.error('WS: Error parsing message data', e);
        }
    };

    ws.current.onerror = (err) => console.error(`WS: Error for client ${clientId}:`, err);
    ws.current.onclose = () => console.log(`WS: Connection closed for client ${clientId}`);

    return () => {
        if (ws.current) {
            console.log(`WS: Closing connection for client ${clientId}`);
            ws.current.close();
        }
    };
}, [clientId]); // The dependency array is now stable

    const handleSendMessage = useCallback(async (content: string) => {
        if (!content.trim() || !selectedClient) return;
        setIsSending(true);
        const optimisticMessage: Message = { id: `agent-${Date.now()}`, client_id: selectedClient.id, content, direction: 'outbound', status: 'pending', created_at: new Date().toISOString() };
        
        setConversationData(prevData => ({
            ...(prevData || { messages: [], immediate_recommendations: null, active_plan: null }),
            messages: [...(prevData?.messages || []), optimisticMessage],
            immediate_recommendations: null,
        }));

        try {
            await api.post(`/api/conversations/${selectedClient.id}/send_reply`, { content });
            setTimeout(() => fetchConversationData(selectedClient.id), 1000);
            refreshConversations(); // Also refresh the sidebar conversations
        } catch (err) {
            console.error("Failed to send message:", err);
            setConversationData(prev => {
                if (!prev) return null;
                return { ...prev, messages: prev.messages.filter(m => m.id !== optimisticMessage.id) };
            });
            alert("Failed to send message.");
        } finally {
            setIsSending(false);
        }
    }, [selectedClient, api, fetchConversationData]);

    const handlePlanAction = useCallback(async (action: 'approve' | 'dismiss', planId: string) => {
        if (!selectedClient) return;
        setIsPlanProcessing(true); // Spinner starts for both actions
        setIsPlanSuccess(false);
        
        try {
            if (action === 'approve') {
                await api.post(`/api/campaigns/${planId}/approve`, {});
                setIsPlanSuccess(true); // Show success message
                // Fetch new data immediately instead of waiting
                fetchConversationData(selectedClient.id);
                // Hide the success message after 3 seconds, but the spinner is already stopped
                setTimeout(() => setIsPlanSuccess(false), 3000);
            } else { // 'dismiss'
                await api.put(`/api/campaigns/${planId}`, { status: 'cancelled' });
                fetchConversationData(selectedClient.id);
            }
        } catch (error) {
            console.error(`Failed to ${action} plan:`, error);
            alert(`Failed to ${action} the plan.`);
        } finally {
            // CRITICAL FIX: Always stop the spinner regardless of action type
            setIsPlanProcessing(false);
        }
    }, [selectedClient, api, fetchConversationData]);

    const handleClientUpdate = useCallback((updatedClient: Client) => {
        setSelectedClient(updatedClient);
        updateClientInList(updatedClient);
        if (selectedClient) fetchConversationData(selectedClient.id);
    }, [updateClientInList, fetchConversationData, selectedClient]);
    
    const handleCoPilotActionSuccess = useCallback(() => {
        if (selectedClient) fetchConversationData(selectedClient.id);
    }, [fetchConversationData, selectedClient]);

    if (pageState === 'loading') {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full text-brand-text-muted p-4">
                <Loader2 className="w-12 h-12 animate-spin mb-4" />
                <p>Loading Conversation...</p>
            </div>
        );
    }
    
    if (pageState === 'error' || !selectedClient) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full text-brand-text-muted p-4">
                <Users className="w-16 h-16 mb-4" />
                <h1 className="text-xl font-medium text-center">Client Not Found</h1>
                <p className="text-sm text-center">The selected client could not be found.</p>
            </div>
        );
    }
    
    const activePlan = conversationData?.active_plan;
    
    // --- LAYOUT FIX: The Intel sidebar is now a sibling to the main content area ---
    const IntelSidebarContent = () => (
        <>
            <DynamicTaggingCard client={selectedClient} onUpdate={handleClientUpdate} />
            <ClientIntelCard client={selectedClient} onUpdate={handleClientUpdate} onReplan={() => {}} displayConfig={displayConfig} />
            <RelationshipCampaignCard 
                plan={activePlan || null}
                messages={scheduledMessages}
                onApprovePlan={(planId) => handlePlanAction('approve', planId)}
                onDismissPlan={(planId) => handlePlanAction('dismiss', planId)}
                isProcessing={isPlanProcessing}
                isSuccess={isPlanSuccess}
                onViewScheduled={() => router.push('/nudges?tab=scheduled')}
                displayConfig={displayConfig}
            />
            <InfoCard title={displayConfig?.properties?.title || 'Properties'}>
                <ul className="space-y-4">
                    {properties.slice(0, 3).map(property => (<li key={property.id} className="flex items-center gap-4"><div className="relative w-20 h-16 bg-brand-dark rounded-md overflow-hidden flex-shrink-0"><Image src={property.image_urls?.[0] || `https://placehold.co/300x200/0B112B/C4C4C4?text=${property.address.split(',')[0]}`} alt={`Image of ${property.address}`} layout="fill" objectFit="cover" /></div><div><h4 className="font-semibold text-brand-text-main truncate">{property.address}</h4><p className="text-sm text-brand-text-muted">${property.price.toLocaleString()}</p><p className="text-xs text-brand-accent font-medium">{property.status}</p></div></li>))}
                </ul>
            </InfoCard>
        </>
    );

    return (
        <div className="flex-1 flex min-w-0 h-full">
            <main className="flex-1 flex flex-col min-w-0 lg:border-l lg:border-r border-white/10">
                <header className="flex items-center justify-between p-4 border-b border-white/10 bg-brand-dark/50 backdrop-blur-sm sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <button onClick={() => setIsSidebarOpen(true)} className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden"><Menu className="w-6 h-6" /></button>
                        <Avatar name={selectedClient.full_name} className="w-11 h-11 hidden sm:flex" />
                        <div>
                            <h2 className="text-xl font-bold text-brand-text-main">{selectedClient.full_name}</h2>
                            <p className="text-sm text-brand-accent">Online</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10"><Phone className="w-5 h-5" /></button>
                        <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10"><Video className="w-5 h-5" /></button>
                    </div>
                </header>

                <div className="flex-shrink-0 p-2 border-b border-white/10 lg:hidden">
                    <Tabs options={tabOptions} activeTab={activeTab} setActiveTab={(id) => setActiveTab(id as 'messages' | 'intel')} />
                </div>

                {/* --- LAYOUT FIX: Conditional rendering for mobile vs. desktop --- */}
                <div className={clsx("flex flex-col flex-grow min-h-0", activeTab === 'messages' ? 'flex' : 'hidden lg:flex')}>
                    <ChatHistory 
                        messages={conversationData?.messages || []}
                        selectedClient={selectedClient}
                        recommendations={conversationData?.immediate_recommendations || null}
                        onActionComplete={handleClientUpdate}
                        onCoPilotActionSuccess={handleCoPilotActionSuccess}
                        onSendMessage={handleSendMessage}
                        messageComposerRef={messageComposerRef}
                    />
                    <MessageComposer onSendMessage={handleSendMessage} isSending={isSending} ref={messageComposerRef} />
                </div>
                
                {/* This is the intel view for mobile only */}
                <div className={clsx("p-6 space-y-6 overflow-y-auto lg:hidden", activeTab === 'intel' ? 'block' : 'hidden')}>
                    <IntelSidebarContent />
                </div>
            </main>

            {/* This is the permanent right sidebar for desktop */}
            <aside className="w-96 flex-shrink-0 border-l border-white/10 p-6 space-y-6 overflow-y-auto hidden lg:flex flex-col">
                <IntelSidebarContent />
            </aside>
        </div>
    );
}
