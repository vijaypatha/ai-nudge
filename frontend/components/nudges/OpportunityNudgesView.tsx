// frontend/components/nudges/OpportunityNudgesView.tsx
'use client';

import { useState, FC, ReactNode, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ActionDeck } from './ActionDeck';
import { BrainCircuit, Sparkles, Home, TrendingUp, BookOpen } from 'lucide-react';

export type DisplayConfig = Record<string, { icon: string; color: string; title: string; }>;

const ICONS: Record<string, ReactNode> = {
    Home: <Home size={16} />,
    Sparkles: <Sparkles size={16} />,
    TrendingUp: <TrendingUp size={16} />,
    BookOpen: <BookOpen size={16} />,
    Default: <Sparkles size={16} />,
};

export interface ClientNudgeSummary {
    client_id: string;
    client_name: string;
    consolidated_nudge_id: string | null;
    total_nudges: number;
    nudge_type_counts: Record<string, number>;
}

interface ClientOpportunitiesCardProps {
    clientName: string;
    opportunityCounts: Record<string, number>;
    totalOpportunities: number;
    onClick: () => void;
    displayConfig: DisplayConfig;
}

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
                 <h3 className="font-bold text-lg text-brand-white">{clientName}</h3>
                <div className="flex-shrink-0 bg-primary-action text-white text-xs font-bold px-2.5 py-1 rounded-full">{totalOpportunities} Total</div>
            </div>
            <div className="flex flex-wrap gap-2">
                {Object.entries(opportunityCounts).map(([type, count]) => {
                    // --- THIS IS THE FIX ---
                    // It now correctly looks for the consolidated nudge type first,
                    // ensuring the UI can find and display the main opportunity nudge.
                    const config = displayConfig[type] || displayConfig['consolidated_initial_matches'];
                    if (!config) return null;
                    return (
                        <div key={type} className={`flex items-center gap-1.5 text-xs font-medium ${config.color} bg-black/20 px-2 py-1 rounded-md`}>
                            {ICONS[config.icon] || ICONS.Default}
                            <span>{count} {type === 'consolidated_initial_matches' ? 'Matches' : config.title}</span>
                        </div>
                    );
                })}
            </div>
        </motion.button>
    );
};

interface OpportunityNudgesViewProps {
    clientSummaries: ClientNudgeSummary[];
    isLoading: boolean;
    onAction: () => void;
    displayConfig: DisplayConfig;
}

export const OpportunityNudgesView: FC<OpportunityNudgesViewProps> = ({ clientSummaries, isLoading, onAction, displayConfig }) => {
    const [activeBriefingId, setActiveBriefingId] = useState<string | null>(null);

    const handleClientSelect = (summary: ClientNudgeSummary) => {
        if (summary.consolidated_nudge_id) {
            setActiveBriefingId(summary.consolidated_nudge_id);
        } else {
            // This case should be rare now, but good to have a fallback.
            const firstNudgeId = Object.keys(summary.nudge_type_counts)[0];
             alert("This client has nudges, but no consolidated match list to display yet.");
        }
    };

    const handleCloseDeck = () => {
        setActiveBriefingId(null);
        onAction(); 
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
    
    return (
        <>
            {activeBriefingId && (
                <ActionDeck
                    key={activeBriefingId} 
                    briefingId={activeBriefingId}
                    onClose={handleCloseDeck}
                    displayConfig={displayConfig}
                />
            )}
            
            <motion.div 
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
                        onClick={() => handleClientSelect(summary)}
                        displayConfig={displayConfig}
                    />
                ))}
            </motion.div>
        </>
    );
};