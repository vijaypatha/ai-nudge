// frontend/components/nudges/ActionDeck.tsx
// --- NEW COMPONENT FILE ---

'use client';

import { useState, useEffect, useMemo, FC, ReactNode } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { CampaignBriefing, Client } from '@/context/AppContext';
import { ManageAudienceModal } from '@/components/modals/ManageAudienceModal';

// --- ICONS ---
import {
    User as UserIcon, Sparkles, Send, X, Users, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, Edit, DollarSign, Target, Check, ChevronsRight, BedDouble, Bath
} from 'lucide-react';

// --- TYPE DEFINITIONS ---
interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reason: string; }

// --- DESIGN SYSTEM ---
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
const BRAND_ACCENT_COLOR = '#20D5B3';

// --- HELPER COMPONENTS ---

const Avatar = ({ name, className }: { name: string; className?: string }) => {
  const initials = name?.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase() || '';
  return <div className={clsx('flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none', className)}>{initials}</div>;
};

const IntelStat: FC<{ icon?: ReactNode; label: string; value: string | number; className?: string }> = ({ icon, label, value, className }) => (
    <div className={`flex items-start gap-3 ${className}`}>
        {icon && <div className="mt-1 flex-shrink-0 text-brand-text-muted">{icon}</div>}
        <div><p className="text-sm font-medium text-brand-text-muted">{label}</p><p className="font-bold text-lg text-brand-text-main">{value}</p></div>
    </div>
);

interface PersuasiveCommandCardProps {
    briefing: CampaignBriefing;
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void;
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>;
}

const PersuasiveCommandCard: FC<PersuasiveCommandCardProps> = ({ briefing, onBriefingUpdate, onAction }) => {
    const config = NUDGE_TYPE_CONFIG[briefing.campaign_type] || NUDGE_TYPE_CONFIG.price_drop;
    const [draft, setDraft] = useState(briefing.edited_draft || briefing.original_draft || '');
    const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);

    useEffect(() => { setDraft(briefing.edited_draft || briefing.original_draft || ''); }, [briefing.id, briefing.original_draft, briefing.edited_draft]);

    const imageUrl = useMemo(() => { const imageUrls = briefing.key_intel?.image_urls; return Array.isArray(imageUrls) && imageUrls.length > 0 ? imageUrls[0] : null; }, [briefing.key_intel]);
    const intel = briefing.key_intel || {};
    const price = intel.price ? `$${Number(intel.price).toLocaleString()}` : null;
    const beds = intel.bedrooms ? Number(intel.bedrooms) : null;
    const baths = intel.bathrooms ? Number(intel.bathrooms) : null;
    const sqft = intel.sqft ? `${Number(intel.sqft).toLocaleString()} sqft` : null;

    const handleDraftChange = (newDraft: string) => { setDraft(newDraft); onBriefingUpdate({ ...briefing, edited_draft: newDraft }); };
    const handleSaveAudience = async (newAudience: Client[]) => {
        const updatedMatchedAudience: MatchedClient[] = newAudience.map(c => ({ client_id: c.id, client_name: c.full_name, match_score: 0, match_reason: 'Manually selected' }));
        onBriefingUpdate({ ...briefing, matched_audience: updatedMatchedAudience });
    };

    return (
        <>
            <ManageAudienceModal isOpen={isAudienceModalOpen} onClose={() => setIsAudienceModalOpen(false)} onSave={handleSaveAudience} initialSelectedClientIds={new Set(briefing.matched_audience.map(c => c.client_id))} />
            <div className="absolute w-full h-full bg-brand-primary border border-white/10 rounded-xl overflow-hidden flex flex-col shadow-2xl">
                <div className="flex-shrink-0 p-4 bg-black/30 border-b border-white/10 flex items-center justify-between"><div className="flex items-center gap-3"><span className={config.color}>{config.icon}</span><h3 className="font-bold text-lg text-brand-text-main">{briefing.headline}</h3></div></div>
                <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-x-6 overflow-y-auto">
                    <div className="p-5 space-y-5 border-r border-white/5">{imageUrl && (<div className="relative w-full h-48 rounded-lg overflow-hidden"><Image src={imageUrl} alt={`Property at ${briefing.headline}`} layout="fill" objectFit="cover" className="bg-white/5"/></div>)}<div className="space-y-1"><h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Target size={16}/>Strategic Summary</h4><p className="text-brand-text-main text-base">This is a key market event relevant to your clients.</p></div><div className="space-y-4 pt-2"><h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><ChevronsRight size={16}/>Key Intel</h4><div className="grid grid-cols-2 gap-4">{price && <IntelStat icon={<DollarSign size={20}/>} label="Price" value={price} />}{beds && <IntelStat icon={<BedDouble size={20}/>} label="Beds" value={beds} />}{baths && <IntelStat icon={<Bath size={20}/>} label="Baths" value={baths} />}{sqft && <IntelStat label="SqFt" value={sqft} />}</div></div></div>
                    <div className="p-5 space-y-5 flex flex-col">
                        <div><button onClick={() => setIsAudienceModalOpen(true)} className="w-full flex items-center justify-center gap-2 p-2 text-sm font-semibold text-brand-text-muted bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:text-brand-text-main transition-colors mb-3"><Users size={16}/>Manage Audience</button><div className="space-y-3 max-h-40 overflow-y-auto pr-2">{briefing.matched_audience.map(client => (<div key={client.client_id}><p className="font-semibold text-brand-text-main text-base">{client.client_name}</p><p className={`text-sm ${config.color} flex items-center gap-1.5`}><Check size={14}/>{client.match_reason}</p></div>))}</div></div>
                        <div className="flex-grow flex flex-col"><h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2 mb-3"><Edit size={16}/>Draft Message</h4><textarea value={draft} onChange={(e) => handleDraftChange(e.target.value)} className="w-full flex-grow bg-brand-dark border border-white/10 rounded-md focus:ring-2 focus:ring-primary-action text-brand-text-main text-base p-3 resize-none"/></div>
                    </div>
                </div>
                <div className="flex-shrink-0 p-3 bg-black/30 border-t border-white/10 grid grid-cols-2 gap-3"><button onClick={() => onAction(briefing, 'dismiss')} className="p-3 bg-white/5 border border-white/10 text-brand-text-main rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-white/10 hover:border-white/20 transition-all duration-200"><X size={18} /> Dismiss Nudge</button><button onClick={() => onAction(briefing, 'send')} className="p-3 text-brand-dark rounded-lg font-bold flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(32,213,179,0.4)] hover:scale-[1.03] transition-all duration-200" style={{ backgroundColor: BRAND_ACCENT_COLOR }}><Send size={18} /> Send to {briefing.matched_audience.length} Client(s)</button></div>
            </div>
        </>
    );
};

interface ActionDeckProps { 
    briefings: CampaignBriefing[]; 
    onClose: () => void; 
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>; 
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void; 
}

export const ActionDeck: FC<ActionDeckProps> = ({ briefings, onClose, onAction, onBriefingUpdate }) => {
    const [cardIndex, setCardIndex] = useState(0);
    const handleActionComplete = async (briefing: CampaignBriefing, action: 'send' | 'dismiss') => { 
        try { 
            await onAction(briefing, action); 
            if (cardIndex < briefings.length - 1) { 
                setCardIndex(cardIndex + 1); 
            } else { 
                onClose(); 
            } 
        } catch (error) { 
            console.error(`ActionDeck Error: Failed to ${action} campaign ${briefing.id}`, error); 
        } 
    };
    return (
        <AnimatePresence>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-brand-dark/60 backdrop-blur-lg flex items-center justify-center z-50 p-4">
                <button onClick={onClose} className="absolute top-4 right-4 text-brand-text-muted hover:text-brand-text-main transition-colors z-50"><X size={32}/></button>
                <div className="absolute top-5 left-5 text-sm font-medium text-brand-text-muted z-50">{cardIndex + 1} of {briefings.length}</div>
                <div className="relative w-full max-w-4xl h-[90vh] max-h-[750px]">
                    <AnimatePresence mode="wait">
                        {cardIndex < briefings.length && (
                            <motion.div 
                                key={briefings[cardIndex].id} 
                                initial={{ scale: 0.95, y: 50, opacity: 0 }} 
                                animate={{ scale: 1, y: 0, opacity: 1 }} 
                                exit={{ scale: 0.95, y: -50, opacity: 0 }} 
                                transition={{ type: "spring", stiffness: 300, damping: 30 }} 
                                className="absolute inset-0"
                            >
                                <PersuasiveCommandCard 
                                    briefing={briefings[cardIndex]} 
                                    onBriefingUpdate={onBriefingUpdate} 
                                    onAction={handleActionComplete} 
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};
