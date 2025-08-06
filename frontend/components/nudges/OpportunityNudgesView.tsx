// frontend/components/nudges/OpportunityNudgesView.tsx
// --- FINAL VERSION: Displays client summaries and passes context to the ActionDeck ---

'use client';

import { useState, FC, ReactNode, useCallback } from 'react';
import { motion } from 'framer-motion';
import { CampaignBriefing as CampaignBriefingType, useAppContext } from '@/context/AppContext';
import { ActionDeck } from './ActionDeck';
import { BrainCircuit, Sparkles, Home, TrendingUp, RotateCcw, TimerOff, CalendarPlus, Archive, User as UserIcon, BookOpen } from 'lucide-react';

export type DisplayConfig = Record<string, {
    icon: string;
    color: string;
    title: string;
}>;

const ICONS: Record<string, ReactNode> = {
    Home: <Home size={16} />,
    Sparkles: <Sparkles size={16} />,
    TrendingUp: <TrendingUp size={16} />,
    RotateCcw: <RotateCcw size={16} />,
    TimerOff: <TimerOff size={16} />,
    CalendarPlus: <CalendarPlus size={16} />,
    Archive: <Archive size={16} />,
    UserIcon: <UserIcon size={16} />,
    BookOpen: <BookOpen size={16} />,
    Default: <Sparkles size={16} />,
};

// This is the full briefing type that the ActionDeck will use
interface ClientNudge extends CampaignBriefingType {
    campaign_id: string;
    headline: string;
    campaign_type: string;
    resource: {
        address?: string;
        price?: number;
        beds?: number;
        baths?: number;
        attributes: Record<string, any>;
    };
    created_at: string;
    updated_at: string;
}

interface ClientOpportunitiesCardProps {
    clientName: string;
    opportunityCounts: Record<string, number>;
    totalOpportunities: number;
    onClick: () => void;
    displayConfig: DisplayConfig;
}

// Renders a single card for a client in the main grid view.
const ClientOpportunitiesCard: FC<ClientOpportunitiesCardProps> = ({ clientName, opportunityCounts, totalOpportunities, onClick, displayConfig }) => {
    return (
        <motion.button
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            onClick={onClick}
            className="w-full text-left p-4 bg-brand-dark/50 border border-white/5 rounded-lg flex flex-col gap-3 transition-all duration-200 hover:bg-brand-dark hover:border-white/10"
        >
            <div className="flex justify-between items-start">
                 <div className="flex items-center gap-3">
                     <h3 className="font-bold text-lg text-brand-white">{clientName}</h3>
                </div>
                <div className="flex-shrink-0 bg-primary-action text-white text-xs font-bold px-2.5 py-1 rounded-full">{totalOpportunities} Total</div>
            </div>
            <div className="flex flex-wrap gap-2">
                {Object.entries(opportunityCounts).map(([type, count]) => {
                    const config = displayConfig[type];
                    if (!config) return null;
                    // Renders the count for each nudge type using the backend-provided display config
                    return (
                        <div key={type} className={`flex items-center gap-1.5 text-xs font-medium ${config.color} bg-black/20 px-2 py-1 rounded-md`}>
                            {ICONS[config.icon] || ICONS.Default}
                            <span>{count} {config.title}</span>
                        </div>
                    );
                })}
            </div>
        </motion.button>
    );
};

interface ClientNudgeSummary {
    client_id: string;
    client_name: string;
    total_nudges: number;
    nudge_type_counts: Record<string, number>;
}

interface OpportunityNudgesViewProps {
    clientSummaries: ClientNudgeSummary[];
    isLoading: boolean;
    onAction: (briefing: CampaignBriefingType, action: 'dismiss' | 'send') => Promise<void>;
    onBriefingUpdate: (updatedBriefing: CampaignBriefingType) => void;
    displayConfig: DisplayConfig;
}

export const OpportunityNudgesView: FC<OpportunityNudgesViewProps> = ({ clientSummaries, isLoading, onAction, onBriefingUpdate, displayConfig }) => {
    const { api } = useAppContext();
    const [activeClient, setActiveClient] = useState<{ id: string, name: string } | null>(null);
    const [activeNudges, setActiveNudges] = useState<ClientNudge[] | null>(null);
    const [isDeckLoading, setIsDeckLoading] = useState(false);

    const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };

    // This function is called when a client card is clicked.
    const handleClientSelect = useCallback(async (clientId: string, clientName: string) => {
        setIsDeckLoading(true);
        setActiveClient({ id: clientId, name: clientName });
        try {
            // It fetches all nudges specifically for the selected client.
            const clientNudgesData = await api.get(`/api/clients/${clientId}/nudges`);
            setActiveNudges(clientNudgesData);
        } catch (err) {
            console.error(`Failed to fetch nudges for client ${clientId}:`, err);
            alert("Could not load the opportunities for this client.");
            setActiveClient(null);
        } finally {
            setIsDeckLoading(false);
        }
    }, [api]);

    const handleCloseDeck = () => {
        setActiveNudges(null);
        setActiveClient(null);
    };

    if (isLoading) {
        return <div className="text-center py-20 text-brand-text-muted">Loading Opportunities...</div>;
    }

    if (clientSummaries.length === 0) {
        return (
            <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
                <BrainCircuit className="mx-auto h-16 w-16 text-brand-text-muted" />
                <h3 className="mt-4 text-xl font-medium text-brand-white">All Clear</h3>
                <p className="mt-1 text-base text-brand-text-muted">The AI is watching the market. Check back soon.</p>
            </div>
        );
    }
    
    // A loading spinner could be displayed here based on `isDeckLoading`
    return (
        <>
            {/* The ActionDeck is only rendered when a client has been selected and their nudges are loaded. */}
            {activeNudges && activeClient && (
                <ActionDeck
                    key={activeClient.id} 
                    initialClientId={activeClient.id}
                    initialClientName={activeClient.name}
                    initialBriefings={activeNudges}
                    onClose={handleCloseDeck}
                    onAction={onAction}
                    displayConfig={displayConfig}
                />
            )}
            
            <motion.div 
                variants={containerVariants} 
                initial="hidden" 
                animate="visible" 
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            >
                {clientSummaries.map((summary) => (
                    <ClientOpportunitiesCard
                        key={summary.client_id}
                        clientName={summary.client_name}
                        opportunityCounts={summary.nudge_type_counts}
                        totalOpportunities={summary.total_nudges}
                        onClick={() => handleClientSelect(summary.client_id, summary.client_name)}
                        displayConfig={displayConfig}
                    />
                ))}
            </motion.div>
        </>
    );
};
