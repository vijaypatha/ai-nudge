// frontend/app/(main)/nudges/page.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppContext, Client, ScheduledMessage, User } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';
import { motion, AnimatePresence } from 'framer-motion';

// --- THIS IS THE FIX ---
// The correct, shared ClientNudgeSummary type is now imported.
import { OpportunityNudgesView, DisplayConfig, ClientNudgeSummary } from '@/components/nudges/OpportunityNudgesView';
import { ScheduledNudgesView } from '@/components/nudges/ScheduledNudgesView';
import { InstantNudgeView } from '@/components/nudges/InstantNudgeView';

// --- THIS IS THE FIX ---
// The incorrect, local definition has been removed.

export default function NudgesPage() {
    const { user, api, loading, socket } = useAppContext();

    // --- THIS IS THE FIX ---
    // The state now uses the correct, imported ClientNudgeSummary type.
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

    useEffect(() => {
        fetchClientSummaries();
        fetchClients();
    }, [fetchClientSummaries, fetchClients]);
    
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
                            onAction={fetchClientSummaries}
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