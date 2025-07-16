// frontend/app/(main)/nudges/page.tsx
// --- AGNOSTIC VERSION ---
// This version now fetches a `display_config` from the API and passes
// it down to its children, making the entire view data-driven.

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppContext, CampaignBriefing, Client, ScheduledMessage, User } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';

import { OpportunityNudgesView, DisplayConfig } from '@/components/nudges/OpportunityNudgesView';
import { ScheduledNudgesView } from '@/components/nudges/ScheduledNudgesView';
import { InstantNudgeView } from '@/components/nudges/InstantNudgeView';

export default function NudgesPage() {
    const { user, clients, api, loading, fetchDashboardData: refetchOpportunities } = useAppContext();
    
    // --- NEW: State for nudges and display_config ---
    const [nudges, setNudges] = useState<CampaignBriefing[]>([]);
    const [displayConfig, setDisplayConfig] = useState<DisplayConfig>({});
    const [isNudgesLoading, setIsNudgesLoading] = useState(true);

    const searchParams = useSearchParams();
    const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'ai_suggestions');
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [isScheduledLoading, setIsScheduledLoading] = useState(true);

    const tabOptions: TabOption[] = [ 
        { id: 'ai_suggestions', label: 'AI Suggestions' },
        { id: 'instant_nudge', label: 'Instant Nudge' }, 
        { id: 'scheduled', label: 'Scheduled' },
    ];

    // --- NEW: Fetching logic now expects the new API response shape ---
    const fetchNudgesAndConfig = useCallback(() => {
        setIsNudgesLoading(true);
        api.get('/api/campaigns?status=DRAFT')
            .then(data => {
                // Expects data in the format: { nudges: [], display_config: {} }
                setNudges(data.nudges || []);
                setDisplayConfig(data.display_config || {});
            })
            .catch(err => console.error("Failed to fetch nudges and config:", err))
            .finally(() => setIsNudgesLoading(false));
    }, [api]);


    const refetchScheduled = useCallback(() => {
        setIsScheduledLoading(true);
        api.get('/api/scheduled-messages/')
            .then(data => {
                const pendingMessages = data.filter((msg: ScheduledMessage) => msg.status === 'pending');
                pendingMessages.sort((a: ScheduledMessage, b: ScheduledMessage) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
                setScheduledMessages(pendingMessages);
            })
            .catch(err => console.error("Failed to fetch scheduled messages:", err))
            .finally(() => setIsScheduledLoading(false));
    }, [api]);

    useEffect(() => {
        fetchNudgesAndConfig();
    }, [fetchNudgesAndConfig]);

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
            fetchNudgesAndConfig(); // Refetch data after action
        } catch (error) {
            console.error(`Failed to ${action} nudge:`, error);
            alert(`Error: Could not ${action} the nudge.`);
        }
    };
    
    // This function is passed down but the logic for updating the briefing array is managed within ActionDeck
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
            
            <div>
                {activeTab === 'ai_suggestions' && (
                    <OpportunityNudgesView 
                        nudges={nudges} 
                        isLoading={isNudgesLoading}
                        onAction={handleAction}
                        onBriefingUpdate={handleBriefingUpdate}
                        displayConfig={displayConfig} // Pass the config down
                    />
                )}
                {activeTab === 'scheduled' && (
                    <ScheduledNudgesView 
                        messages={scheduledMessages} 
                        isLoading={isScheduledLoading} 
                        clients={clients}
                        user={user}
                        onAction={refetchScheduled}
                    />
                )}
                {activeTab === 'instant_nudge' && <InstantNudgeView />}
            </div>
        </main>
    );
}
