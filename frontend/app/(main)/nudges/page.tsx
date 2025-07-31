// frontend/app/(main)/nudges/page.tsx
// --- FINAL VERSION: Uses WebSockets for real-time updates ---

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppContext, Client, ScheduledMessage, User } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';
import { motion, AnimatePresence } from 'framer-motion';

import { OpportunityNudgesView, DisplayConfig } from '@/components/nudges/OpportunityNudgesView';
import { ScheduledNudgesView } from '@/components/nudges/ScheduledNudgesView';
import { InstantNudgeView } from '@/components/nudges/InstantNudgeView';

// Define the extended CampaignBriefing type to include timestamps for our logic.
interface CampaignBriefing extends Omit<import('@/context/AppContext').CampaignBriefing, 'created_at' | 'updated_at'> {
    id: string;
    created_at: string;
    updated_at: string;
}

export default function NudgesPage() {
    // Destructure the 'socket' instance from the AppContext.
    // This assumes your AppContext provides a connected websocket for the user.
    const { user, api, loading, socket } = useAppContext();

    const [nudges, setNudges] = useState<CampaignBriefing[]>([]);
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

    const fetchNudgesAndConfig = useCallback(() => {
        // No need to set loading to true here for refetches,
        // as it would cause a flicker. The initial load is handled below.
        api.get('/api/campaigns?status=DRAFT')
            .then(data => {
                setNudges(data.nudges || []);
                setDisplayConfig(data.display_config || {});
            })
            .catch(err => console.error("Failed to fetch nudges and config:", err))
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
        fetchNudgesAndConfig();
        fetchClients();
    }, [fetchNudgesAndConfig, fetchClients]);
    
    // --- REAL-TIME UPDATE LOGIC ---
    // Listen for messages on the user's websocket connection.
    useEffect(() => {
        if (!socket) return;

        const handleNudgeUpdate = (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                // Check for the specific event broadcasted by our Celery task
                if (data.event === 'nudges_updated') {
                    console.log("WebSocket: Received 'nudges_updated' event. Refetching data.");
                    fetchNudgesAndConfig();
                }
            } catch (error) {
                console.error("WebSocket: Failed to parse message data", error);
            }
        };

        socket.addEventListener('message', handleNudgeUpdate);

        // Cleanup function to prevent memory leaks.
        // This removes the event listener when the component unmounts.
        return () => {
            socket.removeEventListener('message', handleNudgeUpdate);
        };
    }, [socket, fetchNudgesAndConfig]); // Rerun if socket or fetch function changes

    // Fetch scheduled messages only when that tab is active
    useEffect(() => {
        if (activeTab === 'scheduled') {
            // Fetch both in parallel to ensure data consistency
            refetchScheduled();
            fetchClients();
        }
    }, [activeTab, refetchScheduled, fetchClients]);

    const handleAction = async (briefing: CampaignBriefing, action: 'dismiss' | 'send') => {
        try {
            if (action === 'send') {
                await api.put(`/api/campaigns/${briefing.id}`, { edited_draft: briefing.edited_draft, matched_audience: briefing.matched_audience, status: 'approved' });
                await api.post(`/api/campaigns/${briefing.id}/send`, {});
            } else {
                await api.put(`/api/campaigns/${briefing.id}`, { status: 'dismissed' });
            }
            fetchNudgesAndConfig();
        } catch (error) {
            console.error(`Failed to ${action} nudge:`, error);
            alert(`Error: Could not ${action} the nudge.`);
        }
    };

    const handleBriefingUpdate = (updatedBriefing: CampaignBriefing) => {
        setNudges(prevNudges => prevNudges.map(n => n.id === updatedBriefing.id ? updatedBriefing : n));
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
                            nudges={nudges}
                            isLoading={isNudgesLoading}
                            onAction={handleAction}
                            onBriefingUpdate={handleBriefingUpdate}
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
