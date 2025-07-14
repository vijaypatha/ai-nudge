    // frontend/app/(main)/conversations/[clientId]/page.tsx
    // --- DEFINITIVE, COMPLETE VERSION ---

    'use client';

    import { useState, useEffect, useCallback, useRef } from 'react';
    import { useRouter } from 'next/navigation';
    import { find } from 'lodash';
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
    import { Users, Menu, Phone, Video } from 'lucide-react';

    interface ConversationPageProps {
        params: {
            clientId: string;
        };
    }

    interface ConversationData {
        messages: Message[];
        immediate_recommendations: CampaignBriefing | null;
        active_plan: CampaignBriefing | null;
    }

    interface MessageComposerHandle {
        setValue: (value: string) => void;
    }

    export default function ConversationPage({ params }: ConversationPageProps) {
        const { clientId } = params;
        const { loading, api, clients, properties, updateClientInList, refetchScheduledMessagesForClient } = useAppContext();
        const { setIsSidebarOpen } = useSidebar();
        const router = useRouter();
        
        const [error, setError] = useState<string | null>(null);
        const [selectedClient, setSelectedClient] = useState<Client | undefined>(undefined);
        const [conversationData, setConversationData] = useState<ConversationData | null>(null);
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

        const fetchConversationAndScheduled = useCallback(async () => {
            if (!clientId || !api) return;
            try {
                const [convoData, scheduledData] = await Promise.all([
                    api.get(`/api/messages/?client_id=${clientId}`),
                    refetchScheduledMessagesForClient(clientId)
                ]);
                setConversationData(convoData);
                setScheduledMessages(scheduledData);
            } catch (error) {
                console.error("Failed to fetch conversation data:", error);
                setError("Failed to load conversation.");
            }
        }, [clientId, api, refetchScheduledMessagesForClient]);

        useEffect(() => {
            if (clients.length > 0) {
                const client = find(clients, { id: clientId });
                setSelectedClient(client);
            }
        }, [clientId, clients]);

        useEffect(() => {
            if (!selectedClient) return;
            let isMounted = true;
            const pollForUpdates = () => {
                if (isMounted) fetchConversationAndScheduled();
            };
            pollForUpdates();
            const intervalId = setInterval(pollForUpdates, 5000); // Polling interval
            return () => { isMounted = false; clearInterval(intervalId); };
        }, [selectedClient, fetchConversationAndScheduled]);

        const handleSendMessage = useCallback(async (content: string) => {
            if (!content.trim() || !selectedClient) return;
            setIsSending(true);
            const optimisticMessage: Message = { id: `agent-${Date.now()}`, client_id: selectedClient.id, content, direction: 'outbound', status: 'pending', created_at: new Date().toISOString() };
            setConversationData(prevData => ({
                messages: [...(prevData?.messages || []), optimisticMessage],
                immediate_recommendations: null,
                active_plan: prevData?.active_plan || null
            }));
            try {
                await api.post(`/api/conversations/${selectedClient.id}/send_reply`, { content });
                setTimeout(fetchConversationAndScheduled, 1000);
            } catch (err) {
                console.error("Failed to send message:", err);
                setConversationData(prev => {
                    if (!prev) return null;
                    const newMessages = prev.messages.filter(m => m.id !== optimisticMessage.id);
                    return { ...prev, messages: newMessages };
                });
                alert("Failed to send message.");
            } finally {
                setIsSending(false);
            }
        }, [selectedClient, api, fetchConversationAndScheduled]);

        const handlePlanAction = useCallback(async (action: 'approve' | 'dismiss', planId: string) => {
            if (!selectedClient) return;
            setIsPlanProcessing(true);
            setIsPlanSuccess(false);
            try {
                if (action === 'approve') {
                    await api.post(`/api/campaigns/${planId}/approve`, {});
                    setIsPlanSuccess(true);
                    setTimeout(() => {
                        fetchConversationAndScheduled();
                        setIsPlanSuccess(false);
                    }, 3000);
                } else {
                    await api.put(`/api/campaigns/${planId}`, { status: 'cancelled' });
                    fetchConversationAndScheduled();
                }
            } catch (error) {
                console.error(`Failed to ${action} plan:`, error);
                alert(`Failed to ${action} the plan.`);
                setIsPlanProcessing(false);
            } finally {
                if (action !== 'approve') {
                    setIsPlanProcessing(false);
                }
            }
        }, [selectedClient, api, fetchConversationAndScheduled]);

        const handleActionComplete = useCallback((updatedClient: Client) => {
            updateClientInList(updatedClient);
            fetchConversationAndScheduled();
        }, [updateClientInList, fetchConversationAndScheduled]);
        
        const handleCoPilotActionSuccess = useCallback(() => {
            fetchConversationAndScheduled();
        }, [fetchConversationAndScheduled]);

        if (loading && !selectedClient) {
            return <div className="flex-1 flex items-center justify-center text-brand-text-muted">Loading...</div>;
        }
        if (error) {
            return <div className="flex-1 flex items-center justify-center text-red-400">Error: {error}</div>;
        }
        if (!selectedClient) {
            return (
                <div className="flex-1 flex flex-col items-center justify-center h-full text-brand-text-muted p-4">
                    <Users className="w-16 h-16 mb-4" />
                    <h1 className="text-xl font-medium text-center">Client not found</h1>
                </div>
            );
        }
        
        const immediateRecs = conversationData?.immediate_recommendations;
        const activePlan = conversationData?.active_plan;
        
        return (
            <div className="flex-1 flex min-w-0">
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

                    <div className={clsx("flex flex-col flex-grow min-h-0", activeTab === 'messages' ? 'flex' : 'hidden lg:flex')}>
                    <ChatHistory 
                            messages={conversationData?.messages || []}
                            selectedClient={selectedClient}
                            recommendations={immediateRecs || null}
                            onActionComplete={handleActionComplete}
                            onCoPilotActionSuccess={handleCoPilotActionSuccess}
                            onSendMessage={handleSendMessage}
                            messageComposerRef={messageComposerRef}
                    />
                    <MessageComposer onSendMessage={handleSendMessage} isSending={isSending} ref={messageComposerRef} />
                    </div>

                    <div className={clsx("p-6 space-y-6 overflow-y-auto", activeTab === 'intel' ? 'flex flex-col flex-grow' : 'hidden')}>
                        <DynamicTaggingCard client={selectedClient} onUpdate={updateClientInList} />
                        <ClientIntelCard client={selectedClient} onUpdate={updateClientInList} onReplan={() => {}} />
                        <RelationshipCampaignCard 
                            plan={activePlan || null}
                            messages={scheduledMessages}
                            onApprovePlan={(planId) => handlePlanAction('approve', planId)}
                            onDismissPlan={(planId) => handlePlanAction('dismiss', planId)}
                            isProcessing={isPlanProcessing}
                            isSuccess={isPlanSuccess}
                            onViewScheduled={() => router.push('/nudges?tab=scheduled')}
                        />
                    </div>
                </main>

                <aside className="bg-white/5 p-6 flex-col gap-6 overflow-y-auto w-96 flex-shrink-0 hidden lg:flex">
                    <DynamicTaggingCard client={selectedClient} onUpdate={updateClientInList} />
                    <ClientIntelCard client={selectedClient} onUpdate={updateClientInList} onReplan={() => {}} />
                    <RelationshipCampaignCard 
                        plan={activePlan || null}
                        messages={scheduledMessages}
                        onApprovePlan={(planId) => handlePlanAction('approve', planId)}
                        onDismissPlan={(planId) => handlePlanAction('dismiss', planId)}
                        isProcessing={isPlanProcessing}
                        isSuccess={isPlanSuccess}
                        onViewScheduled={() => router.push('/nudges?tab=scheduled')}
                    />
                    <InfoCard title="Properties">
                        <ul className="space-y-4">
                            {properties.slice(0, 3).map(property => (<li key={property.id} className="flex items-center gap-4"><div className="relative w-20 h-16 bg-brand-dark rounded-md overflow-hidden flex-shrink-0"><Image src={property.image_urls?.[0] || `https://placehold.co/300x200/0B112B/C4C4C4?text=${property.address.split(',')[0]}`} alt={`Image of ${property.address}`} layout="fill" objectFit="cover" /></div><div><h4 className="font-semibold text-brand-text-main truncate">{property.address}</h4><p className="text-sm text-brand-text-muted">${property.price.toLocaleString()}</p><p className="text-xs text-brand-accent font-medium">{property.status}</p></div></li>))}
                        </ul>
                    </InfoCard>
                </aside>
            </div>
        );
    }