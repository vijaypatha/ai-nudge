// frontend/app/(main)/nudges/page.tsx
// DEFINITIVE FIX: This version meticulously integrates the reusable <MagicSearchBar />
// into the "Instant Nudge" feature, allowing for dynamic, AI-powered audience creation.

'use client';

import { useState, useEffect, FC, ReactNode, useMemo, useCallback } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { useAppContext } from '@/context/AppContext';
import type { CampaignBriefing, Client } from '@/context/AppContext';
import { Tabs, TabOption } from '@/components/ui/Tabs';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar'; // Import the new search bar
import { ManageAudienceModal } from '@/components/modals/ManageAudienceModal'; // Import the relocated modal

// --- ICONS ---
import {
    User as UserIcon, Sparkles, BrainCircuit, Send, X, ChevronRight, Users, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, Edit, DollarSign, Target, Check, ChevronsRight, BedDouble, Bath, Search, Pencil, Bot, Loader2
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

// --- CORE UI COMPONENTS ---

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
    const { clients } = useAppContext();
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

interface ActionDeckProps { briefings: CampaignBriefing[]; onClose: () => void; onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>; onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void; }

const ActionDeck: FC<ActionDeckProps> = ({ briefings, onClose, onAction, onBriefingUpdate }) => {
    const [cardIndex, setCardIndex] = useState(0);
    const handleActionComplete = async (briefing: CampaignBriefing, action: 'send' | 'dismiss') => { try { await onAction(briefing, action); if (cardIndex < briefings.length - 1) { setCardIndex(cardIndex + 1); } else { onClose(); } } catch (error) { console.error(`ActionDeck Error: Failed to ${action} campaign ${briefing.id}`, error); } };
    return (
        <AnimatePresence>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-brand-dark/60 backdrop-blur-lg flex items-center justify-center z-50 p-4">
                <button onClick={onClose} className="absolute top-4 right-4 text-brand-text-muted hover:text-brand-text-main transition-colors z-50"><X size={32}/></button>
                <div className="absolute top-5 left-5 text-sm font-medium text-brand-text-muted z-50">{cardIndex + 1} of {briefings.length}</div>
                <div className="relative w-full max-w-4xl h-[90vh] max-h-[750px]"><AnimatePresence mode="wait">{cardIndex < briefings.length && (<motion.div key={briefings[cardIndex].id} initial={{ scale: 0.95, y: 50, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.95, y: -50, opacity: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="absolute inset-0"><PersuasiveCommandCard briefing={briefings[cardIndex]} onBriefingUpdate={onBriefingUpdate} onAction={handleActionComplete} /></motion.div>)}</AnimatePresence></div>
            </motion.div>
        </AnimatePresence>
    );
};

interface GroupCardProps { title: string; count: number; config: { color: string }; onClick: () => void; }
const GroupCard: FC<GroupCardProps> = ({ title, count, config, onClick }) => ( <motion.button initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} onClick={onClick} className="w-full text-left p-4 bg-brand-dark/50 border border-white/5 rounded-lg flex items-center gap-4 transition-colors duration-200 hover:bg-brand-dark"><div className="flex-grow"><h4 className="font-semibold text-base text-brand-text-main line-clamp-2">{title.split(': ').slice(1).join(': ')}</h4><p className={`text-sm font-medium ${config.color}`}>{count} {count > 1 ? 'Opportunities' : 'Opportunity'}</p></div><ChevronRight size={20} className="flex-shrink-0 text-brand-text-muted" /></motion.button> );

const InstantNudgeCreator = () => {
    const { clients, api } = useAppContext();
    const [filteredClients, setFilteredClients] = useState<Client[]>(clients);
    const [selectedClients, setSelectedClients] = useState<Set<string>>(new Set());
    const [message, setMessage] = useState('');
    const [topic, setTopic] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => { setFilteredClients(clients); }, [clients]);
    
    const handleAudienceSearch = useCallback(async (query: string) => {
        setIsSearching(true);
        if (!query.trim()) {
            setFilteredClients(clients); // Reset to all clients if query is empty
            setIsSearching(false);
            return;
        }
        try {
            const results = await api.post('/api/clients/search', { natural_language_query: query });
            setFilteredClients(results);
        } catch (error) {
            console.error("Failed to search for clients:", error);
            setFilteredClients([]); // Clear results on error
        } finally {
            setIsSearching(false);
        }
    }, [api, clients]);

    const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked) { setSelectedClients(new Set(filteredClients.map(c => c.id))); } else { setSelectedClients(new Set()); }
    };
    const handleSelectClient = (clientId: string) => {
        const newSelection = new Set(selectedClients);
        if (newSelection.has(clientId)) { newSelection.delete(clientId); } else { newSelection.add(clientId); }
        setSelectedClients(newSelection);
    };

    const handleSendInstantNudge = async () => {
        if (selectedClients.size === 0 || !message.trim()) {
            alert("Please select at least one recipient and write a message.");
            return;
        }
        setIsSending(true);
        const recipients = Array.from(selectedClients);
        const sendPromises = recipients.map(clientId => 
            api.post('/api/campaigns/messages/send-now', { client_id: clientId, content: message })
        );
        try {
            await Promise.all(sendPromises);
            alert(`Successfully sent message to ${recipients.length} client(s).`);
            setSelectedClients(new Set());
            setMessage('');
            setTopic('');
        } catch (error) {
            console.error("Failed to send instant nudge:", error);
            alert("An error occurred while sending the message. Please check the console.");
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="space-y-8 max-w-4xl mx-auto">
            <section>
                <div className="flex items-center gap-3 mb-4"><span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">1</span><h2 className="text-2xl font-bold">Target Your Audience</h2></div>
                <div className="p-6 bg-brand-primary border border-white/10 rounded-xl space-y-4">
                    <label className="text-sm font-semibold text-brand-text-muted">Natural Language Audience Builder ✨</label>
                    <MagicSearchBar onSearch={handleAudienceSearch} isLoading={isSearching} placeholder="e.g., My clients who are avid golfers..."/>
                    <div className="border border-white/10 rounded-lg max-h-64 overflow-y-auto">
                        <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-primary/80 backdrop-blur-sm"><label className="flex items-center gap-3 text-sm"><input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClients.size > 0 && selectedClients.size === filteredClients.length} onChange={handleSelectAll} />Select All Filtered ({selectedClients.size}/{filteredClients.length})</label></div>
                        {isSearching ? (
                            <div className="flex justify-center items-center p-8 text-brand-text-muted"><Loader2 className="animate-spin mr-2" /> Searching...</div>
                        ) : filteredClients.map(client => (<div key={client.id} className="border-b border-white/10 last:border-b-0"><label className="flex items-center gap-3 p-3 hover:bg-white/5 cursor-pointer"><input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClients.has(client.id)} onChange={() => handleSelectClient(client.id)} /><Avatar name={client.full_name} className="w-8 h-8 text-xs"/>{client.full_name}</label></div>))}
                    </div>
                </div>
            </section>
            <section>
                <div className="flex items-center gap-3 mb-4"><span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">2</span><h2 className="text-2xl font-bold">Draft and Send Nudge</h2></div>
                <div className="p-6 bg-brand-primary border border-white/10 rounded-xl space-y-4">
                    <div><label className="text-sm font-semibold text-brand-text-muted" htmlFor="topic">Topic / Goal (for AI draft)</label><input id="topic" type="text" value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g., End of quarter market update" className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"/></div>
                    <div><label className="text-sm font-semibold text-brand-text-muted" htmlFor="message">Message</label><textarea id="message" rows={5} value={message} onChange={e => setMessage(e.target.value)} placeholder="Click 'Draft with AI' or write your own message..." className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"></textarea></div>
                    <div className="flex flex-wrap items-center gap-4"><button className="flex items-center gap-2 p-3 bg-white/10 rounded-md font-semibold hover:bg-white/20"><Bot size={18} /> Draft with AI</button><button onClick={handleSendInstantNudge} disabled={isSending || selectedClients.size === 0 || !message.trim()} className="flex items-center gap-2 p-3 bg-primary-action text-brand-dark rounded-md font-semibold hover:brightness-110 disabled:opacity-50">{isSending ? 'Sending...' : <><Send size={18} /> Send to {selectedClients.size} recipients</>}</button></div>
                </div>
            </section>
        </div>
    );
};

export default function NudgesPage() {
    const { nudges, clients, api, loading, fetchDashboardData } = useAppContext();
    const [activeDeck, setActiveDeck] = useState<CampaignBriefing[] | null>(null);
    const [activeTab, setActiveTab] = useState('ai_suggestions');
    const tabOptions: TabOption[] = [ { id: 'ai_suggestions', label: 'AI Suggestions' }, { id: 'instant_nudge', label: 'Instant Nudge' } ];
    useEffect(() => { if (!loading && nudges.length === 0) { fetchDashboardData(); } }, [loading, nudges, fetchDashboardData]);
    const handleAction = async (briefing: CampaignBriefing, action: 'dismiss' | 'send') => { try { if (action === 'send') { await api.put(`/api/campaigns/${briefing.id}`, { edited_draft: briefing.edited_draft, matched_audience: briefing.matched_audience, status: 'approved' }); await api.post(`/api/campaigns/${briefing.id}/send`, {}); } else { await api.put(`/api/campaigns/${briefing.id}`, { status: 'dismissed' }); } await fetchDashboardData(); setActiveDeck(null); } catch (error) { console.error(`Failed to ${action} nudge:`, error); alert(`Error: Could not ${action} the nudge.`); } };
    const handleBriefingUpdate = (updatedBriefing: CampaignBriefing) => { if (activeDeck) { setActiveDeck(prevDeck => prevDeck?.map(b => b.id === updatedBriefing.id ? updatedBriefing : b) || null); } };
    const groupedByEventType = useMemo(() => nudges.reduce((acc, briefing) => ({ ...acc, [briefing.campaign_type]: [...(acc[briefing.campaign_type] || []), briefing] }), {} as Record<string, CampaignBriefing[]>), [nudges]);
    const groupBriefingsByHeadline = (groupBriefings: CampaignBriefing[]) => groupBriefings.reduce((acc, briefing) => ({ ...acc, [briefing.headline]: [...(acc[briefing.headline] || []), briefing] }), {} as Record<string, CampaignBriefing[]>);
    const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.08 } } };
    const columnVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

    return (
        <main className="flex-1 p-6 sm:p-8 overflow-y-auto">
            {activeDeck && <ActionDeck briefings={activeDeck} onClose={() => setActiveDeck(null)} onAction={handleAction} onBriefingUpdate={handleBriefingUpdate} />}
            <header className="mb-12 flex items-start sm:items-center justify-between gap-4 flex-col sm:flex-row">
                <div>
                    <h1 className="text-4xl sm:text-5xl font-bold text-brand-white tracking-tight">AI Nudges</h1>
                    <p className="text-brand-text-muted mt-2 text-lg">Your AI co-pilot has identified the following revenue opportunities.</p>
                </div>
                <Tabs options={tabOptions} activeTab={activeTab} setActiveTab={setActiveTab} />
            </header>
            <div>
                {activeTab === 'ai_suggestions' && (
                    <>
                        {loading && <div className="text-center py-20 text-brand-text-muted">Loading...</div>}
                        {!loading && nudges.length === 0 && ( <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl"><BrainCircuit className="mx-auto h-16 w-16 text-brand-text-muted" /><h3 className="mt-4 text-xl font-medium text-brand-white">All Clear</h3><p className="mt-1 text-base text-brand-text-muted">The AI is watching the market. Check back soon.</p></div> )}
                        {!loading && nudges.length > 0 && (
                            <motion.div variants={containerVariants} initial="hidden" animate="visible" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {Object.entries(groupedByEventType).map(([type, eventBriefings]) => {
                                    const config = NUDGE_TYPE_CONFIG[type];
                                    if (!config) return null;
                                    const headlineGroups = groupBriefingsByHeadline(eventBriefings);
                                    return (
                                        <motion.div key={type} variants={columnVariants} className="flex flex-col space-y-4 rounded-xl bg-brand-primary border border-white/10 p-4">
                                            <div className="flex items-center justify-between"><div className={`flex items-center gap-2.5 font-bold text-lg ${config.color}`}>{config.icon}<span>{config.title}</span></div><span className="text-sm font-semibold text-brand-white bg-white/10 px-2.5 py-1 rounded-full">{eventBriefings.length}</span></div>
                                            <div className="space-y-3">{Object.entries(headlineGroups).map(([headline, groupBriefings]) => (<GroupCard key={headline} title={headline} count={groupBriefings.length} config={config} onClick={() => setActiveDeck(groupBriefings)} />))}</div>
                                        </motion.div>
                                    );
                                })}
                            </motion.div>
                        )}
                    </>
                )}
                {activeTab === 'instant_nudge' && <InstantNudgeCreator />}
            </div>
        </main>
    );
}
