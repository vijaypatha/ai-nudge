// frontend/components/nudges/OpportunityNudgesView.tsx
// --- NEW COMPONENT ---

'use client';

import { useState, useMemo, FC, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { CampaignBriefing } from '@/context/AppContext';
import { ActionDeck } from './ActionDeck'; // Assuming ActionDeck is extracted to its own component

// --- ICONS ---
import {
    Sparkles, BrainCircuit, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, User as UserIcon, ChevronRight
} from 'lucide-react';

const NUDGE_TYPE_CONFIG: Record<string, { icon: ReactNode; color: string; title: string; }> = {
    'price_drop': { icon: <Sparkles size={20} />, color: 'text-primary-action', title: 'Price Drops' },
    'sold_listing': { icon: <TrendingUp size={20} />, color: 'text-primary-action', title: 'Sold Listings' },
    'new_listing': { icon: <Home size={20} />, color: 'text-primary-action', title: 'New Listings' },
    'back_on_market': { icon: <RotateCcw size={20} />, color: 'text-primary-action', title: 'Back on Market' },
    'expired_listing': { icon: <TimerOff size={20} />, color: 'text-red-500', title: 'Expired Listings' },
    'coming_soon': { icon: <CalendarPlus size={20} />, color: 'text-primary-action', title: 'Coming Soon' },
    'withdrawn_listing': { icon: <Archive size={20} />, color: 'text-brand-text-muted', title: 'Withdrawn' },
    'recency_nudge': { icon: <UserIcon size={20} />, color: 'text-amber-400', title: 'Relationship' },
};

interface GroupCardProps { title: string; count: number; config: { color: string }; onClick: () => void; }
const GroupCard: FC<GroupCardProps> = ({ title, count, config, onClick }) => (
    <motion.button
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        onClick={onClick}
        className="w-full text-left p-4 bg-brand-dark/50 border border-white/5 rounded-lg flex items-center gap-4 transition-colors duration-200 hover:bg-brand-dark"
    >
        <div className="flex-grow">
            <h4 className="font-semibold text-base text-brand-text-main line-clamp-2">{title.split(': ').slice(1).join(': ')}</h4>
            <p className={`text-sm font-medium ${config.color}`}>{count} {count > 1 ? 'Opportunities' : 'Opportunity'}</p>
        </div>
        <ChevronRight size={20} className="flex-shrink-0 text-brand-text-muted" />
    </motion.button>
);

interface OpportunityNudgesViewProps {
    nudges: CampaignBriefing[];
    isLoading: boolean;
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>;
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void;
}

export const OpportunityNudgesView: FC<OpportunityNudgesViewProps> = ({ nudges, isLoading, onAction, onBriefingUpdate }) => {
    const [activeDeck, setActiveDeck] = useState<CampaignBriefing[] | null>(null);

    const groupedByEventType = useMemo(() => nudges.reduce((acc, briefing) => {
        const type = briefing.campaign_type;
        if (!acc[type]) acc[type] = [];
        acc[type].push(briefing);
        return acc;
    }, {} as Record<string, CampaignBriefing[]>), [nudges]);

    const groupBriefingsByHeadline = (groupBriefings: CampaignBriefing[]) => groupBriefings.reduce((acc, briefing) => {
        const headline = briefing.headline;
        if (!acc[headline]) acc[headline] = [];
        acc[headline].push(briefing);
        return acc;
    }, {} as Record<string, CampaignBriefing[]>);
    
    const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.08 } } };
    const columnVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

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
            {activeDeck && <ActionDeck briefings={activeDeck} onClose={() => setActiveDeck(null)} onAction={onAction} onBriefingUpdate={onBriefingUpdate} />}
            <motion.div variants={containerVariants} initial="hidden" animate="visible" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Object.entries(groupedByEventType).map(([type, eventBriefings]) => {
                    const config = NUDGE_TYPE_CONFIG[type];
                    if (!config) return null;
                    const headlineGroups = groupBriefingsByHeadline(eventBriefings);
                    return (
                        <motion.div key={type} variants={columnVariants} className="flex flex-col space-y-4 rounded-xl bg-brand-primary border border-white/10 p-4">
                            <div className="flex items-center justify-between">
                                <div className={`flex items-center gap-2.5 font-bold text-lg ${config.color}`}>
                                    {config.icon}
                                    <span>{config.title}</span>
                                </div>
                                <span className="text-sm font-semibold text-brand-white bg-white/10 px-2.5 py-1 rounded-full">{eventBriefings.length}</span>
                            </div>
                            <div className="space-y-3">
                                {Object.entries(headlineGroups).map(([headline, groupBriefings]) => (
                                    <GroupCard key={headline} title={headline} count={groupBriefings.length} config={config} onClick={() => setActiveDeck(groupBriefings)} />
                                ))}
                            </div>
                        </motion.div>
                    );
                })}
            </motion.div>
        </>
    );
};
