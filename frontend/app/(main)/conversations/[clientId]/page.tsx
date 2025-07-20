// frontend/app/(main)/conversations/[clientId]/page.tsx
// --- CORRECTED VERSION ---

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
import { ContentSuggestionsCard } from '@/components/conversation/ContentSuggestionsCard';
import { ScheduleMessageModal } from '@/components/modals/ScheduleMessageModal';
import { Avatar } from '@/components/ui/Avatar';
import { InfoCard } from '@/components/ui/InfoCard';
import { Users, Menu, Phone, Video, Loader2 } from 'lucide-react';

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
    const { user, api, token, properties, updateClientInList, refetchScheduledMessagesForClient, refreshConversations } = useAppContext();
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
    
    const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
    const [composerContent, setComposerContent] = useState('');

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
                api.get(`/api/conversations/messages/?client_id=${currentClientId}`),
                refetchScheduledMessagesForClient(currentClientId)
            ]);

            const newConvoState = {
                messages: convoData.messages,
                immediate_recommendations: convoData.immediate_recommendations,
                active_plan: convoData.active_plan,
            };

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
        }
    }, [api, refetchScheduledMessagesForClient]);

    useEffect(() => {
        const fetchClientAndConversation = async () => {
            if (!clientId || !api) return;
            setPageState('loading');
            
            // Add timeout to prevent hanging
            const timeoutId = setTimeout(() => {
                console.warn(`Timeout while fetching client ${clientId}`);
                setPageState('error');
            }, 10000); // 10 second timeout
            
            try {
                const clientData = await api.get(`/api/clients/${clientId}`);
                clearTimeout(timeoutId);
                setSelectedClient(clientData);
                await fetchConversationData(clientId);
                setPageState('loaded');
            } catch (error) {
                clearTimeout(timeoutId);
                console.error("Failed to fetch client:", error);
                // If client doesn't exist, redirect to dashboard
                if (error instanceof Error && error.message.includes('404')) {
                    console.log(`Client ${clientId} not found, redirecting to dashboard`);
                    router.push('/dashboard');
                    return;
                }
                setPageState('error');
            }
        };
        fetchClientAndConversation();
    }, [clientId, api, fetchConversationData, router]);

    const handlersRef = useRef({ fetchConversationData, refreshConversations });

    useEffect(() => {
        handlersRef.current = { fetchConversationData, refreshConversations };
    }, [fetchConversationData, refreshConversations]);

    useEffect(() => {
        if (!clientId || !token) return;

        const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';
        const wsUrl = `${wsBaseUrl}/api/ws/${clientId}?token=${token}`;

        console.log(`WS: Attempting to connect to ${wsUrl}`);
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => console.log(`WS: Connection established for client ${clientId}`);

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if ((data.type === 'NEW_MESSAGE' || data.type === 'MESSAGE_SENT') && data.clientId === clientId) {
                    handlersRef.current.fetchConversationData(clientId);
                    handlersRef.current.refreshConversations();
                } else if (data.type === 'INTEL_UPDATED' && data.clientId === clientId) {
                    handlersRef.current.fetchConversationData(clientId);
                }
            } catch (e) {
                console.error('WS: Error parsing message data', e);
            }
        };

        ws.current.onerror = (err) => console.error(`WS: Error for client ${clientId}:`, err);
        ws.current.onclose = (event) => console.log(`WS: Connection closed for client ${clientId}. Code: ${event.code}`);

        return () => {
            if (ws.current) ws.current.close();
        };
    }, [clientId, token]);

    const handleSendMessage = useCallback(async (content: string) => {
        if (!content.trim() || !selectedClient || isSending) return; // Prevent multiple sends
        setIsSending(true);
        const optimisticMessage: Message = { id: `agent-${Date.now()}`, client_id: selectedClient.id, content, direction: 'outbound', status: 'pending', created_at: new Date().toISOString(), source: 'manual', sender_type: 'user' };
        
        setConversationData(prevData => ({
            ...(prevData || { messages: [], immediate_recommendations: null, active_plan: null }),
            messages: [...(prevData?.messages || []), optimisticMessage],
            immediate_recommendations: null,
        }));

        try {
            await api.post(`/api/conversations/${selectedClient.id}/send_reply`, { content });
            refreshConversations();
        } catch (err) {
            console.error("Failed to send message:", err);
            setConversationData(prev => prev ? { ...prev, messages: prev.messages.filter(m => m.id !== optimisticMessage.id) } : null);
            alert("Failed to send message.");
        } finally {
            setIsSending(false);
        }
    }, [selectedClient, api, fetchConversationData, refreshConversations, isSending]);

    const handleOpenScheduleModal = useCallback((content: string) => {
        setComposerContent(content);
        setIsScheduleModalOpen(true);
    }, []);

    const handleScheduleSuccess = useCallback(() => {
        setIsScheduleModalOpen(false);
        if (selectedClient) {
            refetchScheduledMessagesForClient(selectedClient.id);
        }
        alert("Message scheduled successfully!");
    }, [selectedClient, refetchScheduledMessagesForClient]);

    const handlePlanAction = useCallback(async (action: 'approve' | 'dismiss', planId: string) => {
        if (!selectedClient) return;
        setIsPlanProcessing(true);
        setIsPlanSuccess(false);
        
        try {
            if (action === 'approve') {
                await api.post(`/api/campaigns/${planId}/approve`, {});
                setIsPlanSuccess(true);
                fetchConversationData(selectedClient.id);
                setTimeout(() => setIsPlanSuccess(false), 3000);
            } else {
                await api.put(`/api/campaigns/${planId}`, { status: 'cancelled' });
                fetchConversationData(selectedClient.id);
            }
        } catch (error) {
            console.error(`Failed to ${action} plan:`, error);
            alert(`Failed to ${action} the plan.`);
        } finally {
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
        return <div className="flex-1 flex flex-col items-center justify-center h-full"><Loader2 className="w-12 h-12 animate-spin" /></div>;
    }
    
    if (pageState === 'error' || !selectedClient) {
        return <div className="flex-1 flex flex-col items-center justify-center h-full"><Users className="w-16 h-16" /><h1 className="text-xl">Client Not Found</h1></div>;
    }
    
    const activePlan = conversationData?.active_plan;
    
    const IntelSidebarContent = () => (
        <>
            <DynamicTaggingCard client={selectedClient} onUpdate={handleClientUpdate} />
            <ClientIntelCard client={selectedClient} onUpdate={handleClientUpdate} onReplan={() => {}} displayConfig={displayConfig} />
            <ContentSuggestionsCard 
                clientId={clientId}
                api={api}
                onSendMessage={handleSendMessage}
            />
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
            <ScheduleMessageModal
                isOpen={isScheduleModalOpen}
                onClose={() => setIsScheduleModalOpen(false)}
                onScheduleSuccess={handleScheduleSuccess}
                clientId={clientId}
                initialContent={composerContent}
            />
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
                
                {/* --- CORRECTED JSX STRUCTURE --- */}
                {/* This wrapper div contains both the main content areas for mobile tabs */}
                <div className="flex-1 flex flex-col min-h-0">
                    {/* Mobile: Messages Tab */}
                    <div className={clsx("flex flex-col flex-grow min-h-0", activeTab === 'messages' ? 'flex' : 'hidden lg:flex')}>
                        <ChatHistory 
                            messages={conversationData?.messages || []}
                            selectedClient={selectedClient}
                            recommendations={conversationData?.immediate_recommendations || null}
                            onActionComplete={handleClientUpdate}
                            onCoPilotActionSuccess={handleCoPilotActionSuccess}
                            onSendMessage={handleSendMessage}
                            messageComposerRef={messageComposerRef}
                            isSending={isSending}
                        />
                        <MessageComposer
                            onSendMessage={handleSendMessage}
                            onScheduleMessage={handleOpenScheduleModal}
                            onOpenScheduleModal={handleOpenScheduleModal}
                            isSending={isSending}
                            ref={messageComposerRef}
                        />
                    </div>
                    
                    {/* Mobile: Intel Tab */}
                    <div className={clsx("p-6 space-y-6 overflow-y-auto lg:hidden", activeTab === 'intel' ? 'block' : 'hidden')}>
                        <IntelSidebarContent />
                    </div>
                </div>
            </main>

            {/* This is the permanent right sidebar for desktop */}
            <aside className="w-96 flex-shrink-0 border-l border-white/10 p-6 space-y-6 overflow-y-auto hidden lg:flex flex-col">
                <IntelSidebarContent />
            </aside>
        </div>
    );
}