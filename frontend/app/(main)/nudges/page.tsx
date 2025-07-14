// frontend/app/(main)/nudges/page.tsx
// --- DEFINITIVE, REFACTORED VERSION ---

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppContext, CampaignBriefing, Client, ScheduledMessage } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';

// --- MODIFICATION: Import the new view components ---
import { OpportunityNudgesView } from '@/components/nudges/OpportunityNudgesView';
import { ScheduledNudgesView } from '@/components/nudges/ScheduledNudgesView';
import { InstantNudgeView } from '@/components/nudges/InstantNudgeView';

// Assuming ActionDeck is extracted to its own component if it's used by OpportunityNudgesView
// If not, it should be part of OpportunityNudgesView.tsx
// For this example, we assume it's handled within OpportunityNudgesView.

export default function NudgesPage() {
    const { nudges, clients, api, loading, fetchDashboardData } = useAppContext();
    const searchParams = useSearchParams();
    
    const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'ai_suggestions');
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [isScheduledLoading, setIsScheduledLoading] = useState(true);

    const tabOptions: TabOption[] = [ 
        { id: 'ai_suggestions', label: 'AI Suggestions' }, 
        { id: 'scheduled', label: 'Scheduled' },
        { id: 'instant_nudge', label: 'Instant Nudge' } 
    ];

    useEffect(() => {
        if (activeTab === 'scheduled') {
            setIsScheduledLoading(true);
            api.get('/api/scheduled-messages/')
                .then(data => {
                    const pendingMessages = data.filter((msg: ScheduledMessage) => msg.status === 'pending');
                    pendingMessages.sort((a: ScheduledMessage, b: ScheduledMessage) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
                    setScheduledMessages(pendingMessages);
                })
                .catch(err => console.error("Failed to fetch scheduled messages:", err))
                .finally(() => setIsScheduledLoading(false));
        }
    }, [activeTab, api]);

    useEffect(() => {
        if (!loading) {
            fetchDashboardData();
        }
    }, [loading, fetchDashboardData]);

    const handleAction = async (briefing: CampaignBriefing, action: 'dismiss' | 'send') => {
        try {
            if (action === 'send') {
                await api.put(`/api/campaigns/${briefing.id}`, { edited_draft: briefing.edited_draft, matched_audience: briefing.matched_audience, status: 'approved' });
                await api.post(`/api/campaigns/${briefing.id}/send`, {});
            } else {
                await api.put(`/api/campaigns/${briefing.id}`, { status: 'dismissed' });
            }
            await fetchDashboardData();
        } catch (error) {
            console.error(`Failed to ${action} nudge:`, error);
            alert(`Error: Could not ${action} the nudge.`);
        }
    };

    const handleBriefingUpdate = (updatedBriefing: CampaignBriefing) => {
        // This logic would be passed down to OpportunityNudgesView if it needs to manage an active deck
        // For simplicity, we assume this state is managed within the component itself for now.
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
                        isLoading={loading}
                        onAction={handleAction}
                        onBriefingUpdate={handleBriefingUpdate}
                    />
                )}
                {activeTab === 'scheduled' && (
                    <ScheduledNudgesView 
                        messages={scheduledMessages} 
                        isLoading={isScheduledLoading} 
                        clients={clients} 
                    />
                )}
                {activeTab === 'instant_nudge' && <InstantNudgeView />}
            </div>
        </main>
    );
}
