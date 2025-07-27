// frontend/app/(main)/nudges/page.tsx
// --- CORRECTED VERSION ---

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppContext, CampaignBriefing, Client, ScheduledMessage, User } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';
import { motion, AnimatePresence } from 'framer-motion';

import { OpportunityNudgesView, DisplayConfig } from '@/components/nudges/OpportunityNudgesView';
import { ScheduledNudgesView } from '@/components/nudges/ScheduledNudgesView';
import { InstantNudgeView } from '@/components/nudges/InstantNudgeView';

export default function NudgesPage() {
    const { user, api, loading, fetchDashboardData: refetchOpportunities } = useAppContext();

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
        setIsNudgesLoading(true);
        // This now includes both traditional opportunities AND content recommendations
        // as part of the unified AI suggestions system
        api.get('/api/campaigns?status=DRAFT')
            .then(data => {
                setNudges(data.nudges || []);
                setDisplayConfig(data.display_config || {});
            })
            .catch(err => console.error("Failed to fetch nudges and config:", err))
            .finally(() => setIsNudgesLoading(false));
    }, [api]);

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
                // --- FIX IS HERE ---
                // Sort by 'scheduled_at_utc' instead of the old 'scheduled_at' property.
                pendingMessages.sort((a: ScheduledMessage, b: ScheduledMessage) => new Date(a.scheduled_at_utc).getTime() - new Date(b.scheduled_at_utc).getTime());
                setScheduledMessages(pendingMessages);
            })
            .catch(err => console.error("Failed to fetch scheduled messages:", err))
            .finally(() => setIsScheduledLoading(false));
    }, [api]);

    useEffect(() => {
        fetchNudgesAndConfig();
        fetchClients();
    }, [fetchNudgesAndConfig, fetchClients]);

    useEffect(() => {
        if (activeTab === 'scheduled') {
            refetchScheduled();
        }
    }, [activeTab, refetchScheduled]);

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