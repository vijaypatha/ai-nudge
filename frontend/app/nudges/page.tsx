// File Path: frontend/app/nudges/page.tsx
// --- VISUAL REFINEMENT V4: Brand Alignment
// --- This version updates the entire component to use the user-specified brand color palette.
// --- It replaces the multi-color theme with a unified design based on 'brand-dark' and 'primary-action'.
// --- The 'SquareFoot' icon has been removed, and component styles are adjusted for brand consistency.
// ---

'use client';

import { useState, useEffect, FC, ReactNode, useMemo } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';

// --- ICONS ---
// Removed 'SquareFoot' as it does not exist in lucide-react.
import {
    User as UserIcon, Sparkles, BrainCircuit, Send, X, ChevronRight, Users, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, Edit, DollarSign, Target, Check, ChevronsRight, BedDouble, Bath
} from 'lucide-react';

// --- TYPE DEFINITIONS ---
interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reason: string; }
interface CampaignBriefing {
    id: string; campaign_type: string; headline: string; original_draft: string;
    matched_audience: MatchedClient[];
    status: 'new' | 'insight' | 'approved' | 'dismissed' | 'sent';
    key_intel: { [key: string]: string | number | string[] };
    edited_draft: string | null;
    strategic_summary?: string;
    potential_commission?: number;
}

// --- DESIGN SYSTEM: Nudge Type Configuration ---
// Updated colors to match the new brand palette. The accent color is now consistent.
const NUDGE_TYPE_CONFIG: Record<string, { icon: ReactNode; color: string; title: string; }> = {
    'price_drop': { icon: <Sparkles size={20} />, color: 'text-primary-action', title: 'Price Drops' },
    'sold_listing': { icon: <TrendingUp size={20} />, color: 'text-primary-action', title: 'Sold Listings' },
    'new_listing': { icon: <Home size={20} />, color: 'text-primary-action', title: 'New Listings' },
    'back_on_market': { icon: <RotateCcw size={20} />, color: 'text-primary-action', title: 'Back on Market' },
    'expired_listing': { icon: <TimerOff size={20} />, color: 'text-red-500', title: 'Expired Listings' }, // Kept red for high alert
    'coming_soon': { icon: <CalendarPlus size={20} />, color: 'text-primary-action', title: 'Coming Soon' },
    'withdrawn_listing': { icon: <Archive size={20} />, color: 'text-brand-text-muted', title: 'Withdrawn' },
    'recency_nudge': { icon: <UserIcon size={20} />, color: 'text-amber-400', title: 'Relationship' }, // Kept amber for distinction
};
const BRAND_ACCENT_COLOR = '#20D5B3'; // Using 'primary-action' from config

// --- HELPER COMPONENT: IntelStat ---
const IntelStat: FC<{ icon?: ReactNode; label: string; value: string | number; className?: string }> = ({ icon, label, value, className }) => (
    <div className={`flex items-start gap-3 ${className}`}>
        {icon && <div className="mt-1 flex-shrink-0 text-brand-text-muted">{icon}</div>}
        <div>
            <p className="text-sm font-medium text-brand-text-muted">{label}</p>
            <p className="font-bold text-lg text-brand-text-main">{value}</p>
        </div>
    </div>
);

// --- COMPONENT: PersuasiveCommandCard ---
const PersuasiveCommandCard: FC<{
    briefing: CampaignBriefing;
    onUpdate: (updatedBriefing: CampaignBriefing) => void;
    onDismiss: () => void;
    onSend: () => void;
}> = ({ briefing, onUpdate, onDismiss, onSend }) => {
    const config = NUDGE_TYPE_CONFIG[briefing.campaign_type] || NUDGE_TYPE_CONFIG.price_drop;
    const [draft, setDraft] = useState(briefing.edited_draft || briefing.original_draft || '');

    const imageUrl = useMemo(() => {
        const images = briefing.key_intel?.image_urls;
        return (Array.isArray(images) && images.length > 0) ? images[0] : null;
    }, [briefing.key_intel]);

    const intel = briefing.key_intel || {};
    const price = intel.price ? `$${Number(intel.price).toLocaleString()}` : null;
    const beds = intel.bedrooms as number || null;
    const baths = intel.bathrooms as number || null;
    const sqft = intel.sqft ? `${Number(intel.sqft).toLocaleString()} sqft` : null;

    return (
        <div className="absolute w-full h-full bg-brand-primary border border-white/10 rounded-xl overflow-hidden flex flex-col shadow-2xl">
            <div className="flex-shrink-0 p-4 bg-black/30 border-b border-white/10 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className={config.color}>{config.icon}</span>
                    <h3 className="font-bold text-lg text-brand-text-main">{briefing.headline}</h3>
                </div>
                {briefing.potential_commission && (
                    <div className="flex items-center gap-2 text-brand-accent px-3 py-1 bg-brand-accent/10 border border-brand-accent/20 rounded-md">
                        <DollarSign size={16} />
                        <span className="font-bold text-sm">~${briefing.potential_commission.toLocaleString()} GCI</span>
                    </div>
                )}
            </div>
            <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-x-6 overflow-y-auto">
                <div className="p-5 space-y-5 border-r border-white/5">
                    {imageUrl && (
                        <div className="relative w-full h-48 rounded-lg overflow-hidden">
                            <Image src={imageUrl} alt={`Property at ${briefing.headline}`} layout="fill" objectFit="cover" className="bg-white/5"/>
                        </div>
                    )}
                    <div className="space-y-1">
                        <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Target size={16}/>Strategic Summary</h4>
                        <p className="text-brand-text-main text-base">{briefing.strategic_summary || "This is a key market event relevant to your clients."}</p>
                    </div>
                    <div className="space-y-4 pt-2">
                         <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><ChevronsRight size={16}/>Key Intel</h4>
                         <div className="grid grid-cols-2 gap-4">
                            {price && <IntelStat icon={<DollarSign size={20}/>} label="Price" value={price} />}
                            {beds && <IntelStat icon={<BedDouble size={20}/>} label="Beds" value={beds} />}
                            {baths && <IntelStat icon={<Bath size={20}/>} label="Baths" value={baths} />}
                            {sqft && <IntelStat label="SqFt" value={sqft} />}
                         </div>
                    </div>
                </div>
                <div className="p-5 space-y-5 flex flex-col">
                    <div>
                        <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2 mb-3"><Users size={16}/>Matched Audience</h4>
                        <div className="space-y-3 max-h-40 overflow-y-auto pr-2">
                            {briefing.matched_audience.map(client => (
                                <div key={client.client_id}>
                                    <p className="font-semibold text-brand-text-main text-base">{client.client_name}</p>
                                    <p className={`text-sm ${config.color} flex items-center gap-1.5`}><Check size={14}/>{client.match_reason}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="flex-grow flex flex-col">
                        <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2 mb-3"><Edit size={16}/>Draft Message</h4>
                        <textarea
                            value={draft}
                            onChange={(e) => setDraft(e.target.value)}
                            className="w-full flex-grow bg-brand-dark border border-white/10 rounded-md focus:ring-2 focus:ring-primary-action text-brand-text-main text-base p-3 resize-none"
                        />
                    </div>
                </div>
            </div>
            <div className="flex-shrink-0 p-3 bg-black/30 border-t border-white/10 grid grid-cols-2 gap-3">
                <button onClick={onDismiss} className="p-3 bg-white/5 border border-white/10 text-brand-text-main rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-white/10 hover:border-white/20 transition-all duration-200">
                    <X size={18} /> Dismiss
                </button>
                <button
                    onClick={onSend}
                    className="p-3 text-brand-dark rounded-lg font-bold flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(32,213,179,0.4)] hover:scale-[1.03] transition-all duration-200"
                    style={{ backgroundColor: BRAND_ACCENT_COLOR }}
                >
                    <Send size={18} /> Send to {briefing.matched_audience.length} Client(s)
                </button>
            </div>
        </div>
    );
};

// --- COMPONENT: ActionDeck ---
const ActionDeck: FC<{
    briefings: CampaignBriefing[]; onClose: () => void; onUpdate: (updatedBriefing: CampaignBriefing) => void;
}> = ({ briefings, onClose, onUpdate }) => {
    const [cardIndex, setCardIndex] = useState(0);

    const handleAction = async (action: 'send' | 'dismiss') => {
        const briefing = briefings[cardIndex];
        const status = action === 'send' ? 'approved' : 'dismissed';
        try {
            console.log(`Updating campaign ${briefing.id} to ${status}`);
            onUpdate({ ...briefing, status: action === 'send' ? 'sent' : 'dismissed' });
        } catch (error) { console.error(`Error processing campaign ${briefing.id}:`, error); }
        if (cardIndex < briefings.length - 1) { setCardIndex(cardIndex + 1); } else { onClose(); }
    };

    return (
        <AnimatePresence>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-brand-dark/60 backdrop-blur-lg flex items-center justify-center z-50 p-4">
                <button onClick={onClose} className="absolute top-4 right-4 text-brand-text-muted hover:text-brand-text-main transition-colors z-50">
                    <X size={32}/>
                </button>
                <div className="absolute top-5 left-5 text-sm font-medium text-brand-text-muted z-50">
                    {cardIndex + 1} of {briefings.length}
                </div>
                <div className="relative w-full max-w-4xl h-[90vh] max-h-[750px]">
                    <AnimatePresence mode="wait">
                        {cardIndex < briefings.length && (
                             <motion.div key={cardIndex} initial={{ scale: 0.95, y: 50, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.95, y: -50, opacity: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="absolute inset-0">
                                <PersuasiveCommandCard briefing={briefings[cardIndex]} onUpdate={onUpdate} onDismiss={() => handleAction('dismiss')} onSend={() => handleAction('send')} />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

// --- COMPONENT: GroupCard ---
// Updated to match the cleaner, brand-aligned style.
const GroupCard: FC<{
    title: string; count: number; config: { color: string }; onClick: () => void;
}> = ({ title, count, config, onClick }) => (
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

// --- MAIN PAGE COMPONENT ---
export default function NudgesPage() {
    const [briefings, setBriefings] = useState<CampaignBriefing[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeDeck, setActiveDeck] = useState<CampaignBriefing[] | null>(null);

    useEffect(() => {
        const fetchBriefings = async () => {
            setLoading(true);
            try {
                 const data: CampaignBriefing[] = [
                    { id: '1', campaign_type: 'new_listing', headline: 'New Listing: 123 Maple St, Sunnyvale, CA', original_draft: 'A beautiful new home just hit the market!', matched_audience: [{client_id: 'c1', client_name: 'John Doe', match_score: 0.9, match_reason: 'Looking in Sunnyvale'}], status: 'new', key_intel: {price: 1200000, bedrooms: 3, bathrooms: 2, sqft: 1800, image_urls: ['https://placehold.co/600x400/0B112B/E5E7EB?text=123+Maple+St']}, edited_draft: null, strategic_summary: 'This property matches the client\'s desired location and size requirements perfectly.', potential_commission: 30000 },
                    { id: '2', campaign_type: 'price_drop', headline: 'Price Drop: 456 Oak Ave, Cupertino, CA', original_draft: 'Great news! The price has dropped on this property.', matched_audience: [{client_id: 'c2', client_name: 'Jane Smith', match_score: 0.9, match_reason: 'Budget matches new price'}], status: 'new', key_intel: {price: 2100000, bedrooms: 4, bathrooms: 3, sqft: 2500, image_urls: ['https://placehold.co/600x400/0B112B/E5E7EB?text=456+Oak+Ave']}, edited_draft: null, strategic_summary: 'The recent price reduction makes this home a compelling option for your client.', potential_commission: 52500 },
                    { id: '3', campaign_type: 'sold_listing', headline: 'Just Sold Nearby: 789 Pine Ln, Mountain View, CA', original_draft: 'A similar home just sold nearby, indicating strong market activity.', matched_audience: [{client_id: 'c3', client_name: 'Peter Jones', match_score: 0.9, match_reason: 'Expressed interest in area'}], status: 'new', key_intel: {}, edited_draft: null },
                    { id: '4', campaign_type: 'back_on_market', headline: 'Back on Market: 321 Elm Ct, Palo Alto, CA', original_draft: 'A second chance! This property is back on the market.', matched_audience: [{client_id: 'c4', client_name: 'Mary Williams', match_score: 0.9, match_reason: 'Previously viewed this property'}], status: 'new', key_intel: {price: 3500000, bedrooms: 5, bathrooms: 4, sqft: 3200, image_urls: ['https://placehold.co/600x400/0B112B/E5E7EB?text=321+Elm+Ct']}, edited_draft: null },
                    { id: '5', campaign_type: 'expired_listing', headline: 'Expired Listing: 159 Cedar Pl, Los Altos, CA', original_draft: 'This could be an opportunity. This listing has expired.', matched_audience: [{client_id: 'c5', client_name: 'Sam Brown', match_score: 0.8, match_reason: 'Was interested in similar properties'}], status: 'new', key_intel: {}, edited_draft: null },
                    { id: '6', campaign_type: 'coming_soon', headline: 'Coming Soon: 753 Spruce Dr, San Jose, CA', original_draft: 'Get a head start on this new property coming soon!', matched_audience: [{client_id: 'c6', client_name: 'Chris Green', match_score: 0.95, match_reason: 'Actively looking in this school district'}], status: 'new', key_intel: {}, edited_draft: null },
                    { id: '7', campaign_type: 'withdrawn_listing', headline: 'Withdrawn: 852 Redwood Blvd, Santa Clara, CA', original_draft: 'This property was withdrawn. Might be a chance to connect with the seller.', matched_audience: [{client_id: 'c4', client_name: 'Mary Williams', match_score: 0.7, match_reason: 'Previously inquired about this address'}], status: 'new', key_intel: {}, edited_draft: null },
                    { id: '8', campaign_type: 'recency_nudge', headline: 'Relationship: 3 clients you haven\'t contacted in 90 days', original_draft: 'Just checking in to see how you\'re doing!', matched_audience: [{client_id: 'c7', client_name: 'David Black', match_score: 0, match_reason: 'Past client'}, {client_id: 'c8', client_name: 'Nancy White', match_score: 0, match_reason: 'Past client'}], status: 'new', key_intel: {}, edited_draft: null },
                    { id: '9', campaign_type: 'new_listing', headline: 'New Listing: 654 Birch Rd, Sunnyvale, CA', original_draft: 'Another great listing in a desirable area.', matched_audience: [{client_id: 'c1', client_name: 'John Doe', match_score: 0.9, match_reason: 'Looking in Sunnyvale'}], status: 'new', key_intel: {price: 1350000, bedrooms: 3, bathrooms: 2.5, sqft: 1950, image_urls: ['https://placehold.co/600x400/0B112B/E5E7EB?text=654+Birch+Rd']}, edited_draft: null },
                ];
                setBriefings(data);
            } catch (err) { console.error('Error fetching nudges:', err); }
            finally { setLoading(false); }
        };
        fetchBriefings();
    }, []);

    const handleCampaignUpdate = (updatedBriefing: CampaignBriefing) => {
        setBriefings(prev => prev.filter(b => b.id !== updatedBriefing.id));
        if (activeDeck) {
            const newDeck = activeDeck.filter(b => b.id !== updatedBriefing.id);
            if (newDeck.length > 0) {
                 setActiveDeck(newDeck);
            } else {
                 setActiveDeck(null);
            }
        }
    };

    const groupedByEventType = useMemo(() => {
        return briefings.reduce((acc, briefing) => {
            const type = briefing.campaign_type;
            if (!acc[type]) { acc[type] = []; }
            acc[type].push(briefing);
            return acc;
        }, {} as Record<string, CampaignBriefing[]>);
    }, [briefings]);

    const groupBriefingsByHeadline = (groupBriefings: CampaignBriefing[]) => {
        return groupBriefings.reduce((acc, briefing) => {
            const key = briefing.headline;
            if (!acc[key]) { acc[key] = []; }
            acc[key].push(briefing);
            return acc;
        }, {} as Record<string, CampaignBriefing[]>);
    };

    const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.08 } } };
    const columnVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

    return (
        <>
            {activeDeck && <ActionDeck briefings={activeDeck} onClose={() => setActiveDeck(null)} onUpdate={handleCampaignUpdate}/>}
            <div className="min-h-screen bg-brand-dark text-brand-text-main font-sans">
                <main className="max-w-screen-xl mx-auto p-6 sm:p-8">
                    <header className="mb-12">
                        <h1 className="text-4xl sm:text-5xl font-bold text-brand-white tracking-tight">AI Opportunities</h1>
                        <p className="text-brand-text-muted mt-2 text-lg">Your AI co-pilot has identified the following revenue opportunities.</p>
                    </header>
                    
                    {loading && <div className="text-center py-20 text-brand-text-muted">Loading...</div>}
                    
                    {!loading && briefings.length === 0 && (
                        <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
                            <BrainCircuit className="mx-auto h-16 w-16 text-brand-text-muted" />
                            <h3 className="mt-4 text-xl font-medium text-brand-white">All Clear</h3>
                            <p className="mt-1 text-base text-brand-text-muted">The AI is watching the market. Check back soon.</p>
                        </div>
                    )}

                    {!loading && briefings.length > 0 && (
                        <motion.div
                            variants={containerVariants}
                            initial="hidden"
                            animate="visible"
                            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                        >
                            {Object.entries(groupedByEventType).map(([type, eventBriefings]) => {
                                const config = NUDGE_TYPE_CONFIG[type];
                                if (!config) return null;
                                const headlineGroups = groupBriefingsByHeadline(eventBriefings as CampaignBriefing[]);
                                
                                return (
                                    <motion.div
                                        key={type}
                                        variants={columnVariants}
                                        className="flex flex-col space-y-4 rounded-xl bg-brand-primary border border-white/10 p-4"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className={`flex items-center gap-2.5 font-bold text-lg ${config.color}`}>
                                                {config.icon}
                                                <span>{config.title}</span>
                                            </div>
                                            <span className="text-sm font-semibold text-brand-white bg-white/10 px-2.5 py-1 rounded-full">
                                                {(eventBriefings as any[]).length}
                                            </span>
                                        </div>
                                        <div className="space-y-3">
                                            {Object.entries(headlineGroups).map(([headline, groupBriefings]) => (
                                                <GroupCard
                                                    key={headline}
                                                    title={headline}
                                                    count={(groupBriefings as any[]).length}
                                                    config={config}
                                                    onClick={() => setActiveDeck(groupBriefings as CampaignBriefing[])}
                                                />
                                            ))}
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </motion.div>
                    )}
                </main>
            </div>
        </>
    );
}
