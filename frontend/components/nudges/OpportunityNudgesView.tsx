// frontend/components/nudges/OpportunityNudgesView.tsx
// --- AGNOSTIC VERSION ---
// This component is now "dumb" and receives display configuration as a prop,
// making it reusable for any vertical (real estate, therapy, etc.).

'use client';

import { useState, useMemo, FC, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { CampaignBriefing } from '@/context/AppContext';
import { ActionDeck } from './ActionDeck';
import { BrainCircuit, Sparkles, Home, TrendingUp, RotateCcw, TimerOff, CalendarPlus, Archive, User as UserIcon } from 'lucide-react';

// --- NEW: Define the shape of the config object we expect from the API ---
export type DisplayConfig = Record<string, {
    icon: string; // Icon name (e.g., "Home", "Sparkles")
    color: string;
    title: string;
}>;

// --- NEW: A helper to map string names to actual icon components ---
const ICONS: Record<string, ReactNode> = {
    Home: <Home size={16} />,
    Sparkles: <Sparkles size={16} />,
    TrendingUp: <TrendingUp size={16} />,
    RotateCcw: <RotateCcw size={16} />,
    TimerOff: <TimerOff size={16} />,
    CalendarPlus: <CalendarPlus size={16} />,
    Archive: <Archive size={16} />,
    UserIcon: <UserIcon size={16} />,
    Default: <Sparkles size={16} />,
};

interface ClientOpportunitiesCardProps {
    clientName: string;
    opportunities: CampaignBriefing[];
    onClick: () => void;
    displayConfig: DisplayConfig; // Pass config down to the card
}

const ClientOpportunitiesCard: FC<ClientOpportunitiesCardProps> = ({ clientName, opportunities, onClick, displayConfig }) => {
    const opportunityCounts = useMemo(() => {
        return opportunities.reduce((acc, nudge) => {
            acc[nudge.campaign_type] = (acc[nudge.campaign_type] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);
    }, [opportunities]);

    return (
        <motion.button
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            onClick={onClick}
            className="w-full text-left p-4 bg-brand-dark/50 border border-white/5 rounded-lg flex flex-col gap-3 transition-all duration-200 hover:bg-brand-dark hover:border-white/10"
        >
            <div className="flex justify-between items-start">
                <h3 className="font-bold text-lg text-brand-white">{clientName}</h3>
                <div className="flex-shrink-0 bg-primary-action text-white text-xs font-bold px-2.5 py-1 rounded-full">{opportunities.length} Total</div>
            </div>
            <div className="flex flex-wrap gap-2">
                {Object.entries(opportunityCounts).map(([type, count]) => {
                    const config = displayConfig[type];
                    if (!config) return null;
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

interface OpportunityNudgesViewProps {
    nudges: CampaignBriefing[];
    isLoading: boolean;
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>;
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void;
    displayConfig: DisplayConfig; // Expect the config as a prop
}

export const OpportunityNudgesView: FC<OpportunityNudgesViewProps> = ({ nudges, isLoading, onAction, onBriefingUpdate, displayConfig }) => {
    const [activeDeck, setActiveDeck] = useState<CampaignBriefing[] | null>(null);

    const groupedByClient = useMemo(() => {
        return nudges.reduce((acc, nudge) => {
            nudge.matched_audience.forEach(client => {
                if (!acc[client.client_id]) {
                    acc[client.client_id] = { clientName: client.client_name, opportunities: [] };
                }
                if (!acc[client.client_id].opportunities.some(o => o.id === nudge.id)) {
                    acc[client.client_id].opportunities.push(nudge);
                }
            });
            return acc;
        }, {} as Record<string, { clientName: string; opportunities: CampaignBriefing[] }>);
    }, [nudges]);

    const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };

    if (isLoading) {
        return <div className="text-center py-20 text-brand-text-muted">Loading Opportunities...</div>;
    }

    if (nudges.length === 0) {
        return (
            <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
                <BrainCircuit className="mx-auto h-16 w-16 text-brand-text-muted" />
                <h3 className="mt-4 text-xl font-medium text-brand-white">All Clear</h3>
                <p className="mt-1 text-base text-brand-text-muted">The AI is watching the market. Check back soon.</p>
            </div>
        );
    }

    return (
        <>
            {activeDeck && <ActionDeck briefings={activeDeck} onClose={() => setActiveDeck(null)} onAction={onAction} onBriefingUpdate={onBriefingUpdate} displayConfig={displayConfig} />}
            
            <motion.div 
                variants={containerVariants} 
                initial="hidden" 
                animate="visible" 
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            >
                {Object.entries(groupedByClient).map(([clientId, clientData]) => (
                    <ClientOpportunitiesCard
                        key={clientId}
                        clientName={clientData.clientName}
                        opportunities={clientData.opportunities}
                        onClick={() => setActiveDeck(clientData.opportunities)}
                        displayConfig={displayConfig}
                    />
                ))}
            </motion.div>
        </>
    );
};
