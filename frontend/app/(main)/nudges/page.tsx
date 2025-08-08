// frontend/app/(main)/nudges/page.tsx
// --- FINAL VERSION: Fetches client summaries for the new client-centric view ---

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppContext, Client, ScheduledMessage, User } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';
import { motion, AnimatePresence } from 'framer-motion';

import { OpportunityNudgesView, DisplayConfig } from '@/components/nudges/OpportunityNudgesView';
import { ScheduledNudgesView } from '@/components/nudges/ScheduledNudgesView';
import { InstantNudgeView } from '@/components/nudges/InstantNudgeView';

// Define the structure for the client summary data from the new API endpoint
interface ClientNudgeSummary {
    client_id: string;
    client_name: string;
    total_nudges: number;
    nudge_type_counts: Record<string, number>;
}

// Import the CampaignBriefing type from AppContext
import { CampaignBriefing } from '@/context/AppContext';

export default function NudgesPage() {
    const { user, api, loading, socket } = useAppContext();

    // State now holds client summaries instead of individual nudges
    const [clientSummaries, setClientSummaries] = useState<ClientNudgeSummary[]>([]);
    const [displayConfig, setDisplayConfig] = useState<DisplayConfig>({});
    const [isNudgesLoading, setIsNudgesLoading] = useState(true);

    const searchParams = useSearchParams();
    const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'ai_suggestions');
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [isScheduledLoading, setIsScheduledLoading] = useState(true);

    const [clients, setClients] = useState<Client[]>([]);
    const [isClientsLoading, setIsClientsLoading] = useState(true);

    const tabOptions: TabOption[] = [
        { id: 'ai_suggestions', label: 'My AI Nudges' },
        { id: 'instant_nudge', label: 'Instant Nudge' },
        { id: 'scheduled', label: 'Scheduled' },
    ];

    const fetchClientSummaries = useCallback(() => {
        // Use the new, more efficient client-summary endpoint
        api.get('/api/campaigns/client-summaries')
            .then(data => {
                setClientSummaries(data.client_summaries || []);
                setDisplayConfig(data.display_config || {});
            })
            .catch(err => console.error("Failed to fetch client nudge summaries:", err))
            .finally(() => {
                if (isNudgesLoading) setIsNudgesLoading(false);
            });
    }, [api, isNudgesLoading]);

    const fetchClients = useCallback(() => {
        setIsClientsLoading(true);
        api.get('/api/clients')
            .then(setClients)
            .catch(err => console.error("Failed to fetch clients:", err))
            .finally(() => setIsClientsLoading(false));
    }, [api]);

    const refetchScheduled = useCallback(() => {
        setIsScheduledLoading(true);
        api.get('/api/scheduled-messages/')
            .then(data => {
                const pendingMessages = data.filter((msg: ScheduledMessage) => msg.status === 'pending');
                pendingMessages.sort((a: ScheduledMessage, b: ScheduledMessage) => new Date(a.scheduled_at_utc).getTime() - new Date(b.scheduled_at_utc).getTime());
                setScheduledMessages(pendingMessages);
            })
            .catch(err => console.error("Failed to fetch scheduled messages:", err))
            .finally(() => setIsScheduledLoading(false));
    }, [api]);

    // Initial data fetch on component mount
    useEffect(() => {
        fetchClientSummaries();
        fetchClients();
    }, [fetchClientSummaries, fetchClients]);
    
    // Real-time update logic
    useEffect(() => {
        if (!socket) return;

        const handleNudgeUpdate = (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                if (data.event === 'nudges_updated' || data.event === 'PLAN_UPDATED') {
                    console.log(`WebSocket: Received '${data.event}' event. Refetching client summaries.`);
                    fetchClientSummaries();
                }
            } catch (error) {
                console.error("WebSocket: Failed to parse message data", error);
            }
        };

        socket.addEventListener('message', handleNudgeUpdate);

        return () => {
            socket.removeEventListener('message', handleNudgeUpdate);
        };
    }, [socket, fetchClientSummaries]);

    useEffect(() => {
        if (activeTab === 'scheduled') {
            refetchScheduled();
            fetchClients();
        }
    }, [activeTab, refetchScheduled, fetchClients]);

    const handleAction = async (briefing: CampaignBriefing, action: 'dismiss' | 'send') => {
        try {
            if (action === 'send') {
                const updatePayload = {
                    edited_draft: briefing.edited_draft || briefing.original_draft,
                    matched_audience: briefing.matched_audience,
                    status: 'active' as const
                };
                
                // --- THIS IS THE FIX ---
                // The incorrect test-debug line has been removed.
                // The code now proceeds directly to the correct API calls.
                
                await api.put(`/api/campaigns/${briefing.id}`, updatePayload);
                await api.post(`/api/campaigns/${briefing.id}/send`, {});
    
            } else {
                await api.put(`/api/campaigns/${briefing.id}`, { status: 'dismissed' as const });
            }
            // After an action, refetch the summaries to update the client grid
            fetchClientSummaries();
        } catch (error) {
            console.error(`Failed to ${action} nudge:`, error);
            alert(`Error: Could not ${action} the nudge.`);
        }
    };

    return (
        <main className="flex-1 p-6 sm:p-8 overflow-y-auto">
            <header className="mb-12 flex items-start sm:items-center justify-between gap-4 flex-col sm:flex-row">
                <div>
                    <h1 className="text-4xl sm:text-5xl font-bold text-brand-white tracking-tight">AI Nudges</h1>
                    <p className="text-brand-text-muted mt-2 text-lg">Your AI co-pilot has identified the following revenue opportunities.</p>
                </div>
                <Tabs options={tabOptions} activeTab={activeTab} setActiveTab={setActiveTab} />
            </header>

            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -15 }}
                    transition={{ duration: 0.25 }}
                >
                    {activeTab === 'ai_suggestions' && (
                        <OpportunityNudgesView
                            clientSummaries={clientSummaries}
                            isLoading={isNudgesLoading}
                            onAction={handleAction}
                            // onBriefingUpdate is now managed inside the ActionDeck
                            onBriefingUpdate={() => {}}
                            displayConfig={displayConfig}
                        />
                    )}
                    {activeTab === 'scheduled' && (
                        <ScheduledNudgesView
                            messages={scheduledMessages}
                            isLoading={isScheduledLoading || isClientsLoading}
                            clients={clients}
                            user={user}
                            onAction={refetchScheduled}
                        />
                    )}
                    {activeTab === 'instant_nudge' && <InstantNudgeView clients={clients} onScheduleSuccess={refetchScheduled} />}
                </motion.div>
            </AnimatePresence>
        </main>
    );
}
