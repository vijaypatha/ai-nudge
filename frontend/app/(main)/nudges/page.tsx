// File Path: frontend/app/nudges/page.tsx
// --- FIX for Runtime Error ---
// This version fixes a TypeError caused by an outdated data model.
// --- 1. The 'Client' type has been updated to use 'ai_tags' and 'user_tags'.
// --- 2. The 'uniqueTags' logic in the modal now correctly reads from both tag fields.
// ---

'use client';

import { useState, useEffect, FC, ReactNode, useMemo } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
// Import the useAppContext hook to access global state and API client
import { useAppContext } from '@/context/AppContext';
// Import CampaignBriefing type from AppContext to ensure type consistency across the application
import type { CampaignBriefing } from '@/context/AppContext';


// --- ICONS ---
import {
    User as UserIcon, Sparkles, BrainCircuit, Send, X, ChevronRight, Users, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, Edit, DollarSign, Target, Check, ChevronsRight, BedDouble, Bath, Search, Pencil
} from 'lucide-react';

// --- TYPE DEFINITIONS ---
// MatchedClient remains local as it might be specific to how nudges handle audience details
interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reason: string; }
// UPDATED: The Client type now reflects the new data model with separate tag fields.
// This type is kept local if it's not universally defined or differs slightly from AppContext's client type.
interface Client {
    id: string;
    full_name: string;
    ai_tags: string[];
    user_tags: string[];
}
// CampaignBriefing type is now imported from '@/context/AppContext'

// --- DESIGN SYSTEM: Nudge Type Configuration ---
// Defines display properties for different nudge types
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
// Defines the primary accent color for branding
const BRAND_ACCENT_COLOR = '#20D5B3';

// --- MODAL & HELPER COMPONENTS ---

/**
 * Renders a circular avatar with initials based on a given name.
 * @param {string} name - The full name to generate initials from.
 * @param {string} [className] - Additional CSS classes for styling.
 */
const Avatar = ({ name, className }: { name: string; className?: string }) => {
  const initials = name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase();
  return (
    <div className={clsx('flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none', className)}>
      {initials}
    </div>
  );
};

interface ManageAudienceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newAudience: Client[]) => Promise<void>;
  allClients: Client[];
  initialSelectedClientIds: Set<string>;
}

/**
 * Modal component for managing (selecting/deselecting) clients for a campaign audience.
 */
const ManageAudienceModal = ({ isOpen, onClose, onSave, allClients, initialSelectedClientIds }: ManageAudienceModalProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);
  const [selectedClientIds, setSelectedClientIds] = useState<Set<string>>(initialSelectedClientIds);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Memoized list of unique tags from all available clients
  const uniqueTags = useMemo(() => {
    const allTags = new Set<string>();
    // Iterate over both `ai_tags` and `user_tags` and add them to the set
    (allClients || []).forEach((client) => {
        if (client.ai_tags) client.ai_tags.forEach((tag) => allTags.add(tag));
        if (client.user_tags) client.user_tags.forEach((tag) => allTags.add(tag));
    });
    return Array.from(allTags).sort();
  }, [allClients]);

  // Effect to reset modal state when it opens or initial props change
  useEffect(() => {
    if (isOpen) {
      setSelectedClientIds(initialSelectedClientIds);
      setFilteredClients(allClients);
      setIsSaving(false);
      setError(null);
    }
  }, [isOpen, initialSelectedClientIds, allClients]);

  // Effect to filter clients based on search query and active tags
  useEffect(() => {
    if (!isOpen || !allClients) return;
    const lowerCaseQuery = searchQuery.toLowerCase();
    const newFilteredClients = allClients.filter(client => {
        const matchesQuery = lowerCaseQuery ? client.full_name.toLowerCase().includes(lowerCaseQuery) : true;
        const combinedTags = [...(client.ai_tags || []), ...(client.user_tags || [])];
        const matchesTags = activeTags.size > 0 ? Array.from(activeTags).every(tag => combinedTags.includes(tag)) : true;
        return matchesQuery && matchesTags;
    });
    setFilteredClients(newFilteredClients);
  }, [searchQuery, activeTags, allClients, isOpen]);

  // Handles toggling a tag's active state
  const handleTagClick = (tag: string) => {
    const newTags = new Set(activeTags);
    if (newTags.has(tag)) newTags.delete(tag); else newTags.add(tag);
    setActiveTags(newTags);
  };

  // Handles toggling a client's selection state
  const handleSelectClient = (clientId: string) => {
    const newSelection = new Set(selectedClientIds);
    if (newSelection.has(clientId)) newSelection.delete(clientId); else newSelection.add(clientId);
    setSelectedClientIds(newSelection);
  };

  // Handles selecting/deselecting all currently filtered clients
  const handleSelectAllFiltered = () => {
      const allFilteredIds = new Set(filteredClients.map(c => c.id));
      const isAllSelected = filteredClients.length > 0 && filteredClients.every(c => selectedClientIds.has(c.id));
      const newSelection = new Set(selectedClientIds);
      if (isAllSelected) {
          allFilteredIds.forEach(id => newSelection.delete(id));
      } else {
          allFilteredIds.forEach(id => newSelection.add(id));
      }
      setSelectedClientIds(newSelection);
  };

  // Handles saving the selected audience
  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    const selectedClientObjects = allClients.filter(c => selectedClientIds.has(c.id));
    try {
      await onSave(selectedClientObjects);
      onClose();
    } catch (err) {
      setError("Failed to save audience. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;
  const isAllFilteredSelected = filteredClients.length > 0 && filteredClients.every(c => selectedClientIds.has(c.id));

  return (
    <div className="fixed inset-0 bg-brand-dark/90 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-brand-primary border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <header className="p-6 border-b border-white/10 flex justify-between items-center flex-shrink-0">
          <h2 className="text-2xl font-bold text-brand-text-main">Manage Audience</h2>
          <button onClick={onClose} className="text-brand-text-muted hover:text-white"><X size={24} /></button>
        </header>
        <div className="p-6 space-y-4 flex-shrink-0">
          <div className="relative">
            <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-brand-text-muted" />
            <input type="text" placeholder="Search by name..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full bg-black/20 border border-white/20 rounded-lg p-3 pl-10 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"/>
          </div>
          <div className="flex flex-wrap gap-2">
            {uniqueTags.map((tag) => ( <button key={tag} onClick={() => handleTagClick(tag)} className={clsx('px-3 py-1.5 text-sm font-semibold rounded-full border transition-colors', activeTags.has(tag) ? 'bg-brand-accent text-brand-dark border-brand-accent' : 'bg-white/5 border-white/10 text-brand-text-muted hover:border-white/30')}> {tag} </button>))}
          </div>
        </div>
        <div className="px-6 pb-2 flex-grow overflow-y-auto">
          <div className="border border-white/10 rounded-lg">
            <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-primary/80 backdrop-blur-sm">
                <label className="flex items-center gap-3 text-sm font-semibold cursor-pointer text-white">
                    <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent focus:ring-offset-brand-primary" checked={isAllFilteredSelected} onChange={handleSelectAllFiltered}/>
                    Select All ({selectedClientIds.size} selected)
                </label>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {filteredClients.length === 0 ? (<p className="p-4 text-center text-brand-text-muted">No clients found.</p>)
              : (filteredClients.map((client) => (
                  <div key={client.id} className="border-b border-white/10 last:border-b-0">
                    <label className="flex items-center gap-3 p-3 hover:bg-white/5 cursor-pointer">
                      <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClientIds.has(client.id)} onChange={() => handleSelectClient(client.id)}/>
                      <Avatar name={client.full_name} className="w-8 h-8 text-xs" />
                      <span className="text-base text-brand-text-main">{client.full_name}</span>
                    </label>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
        <footer className="p-6 border-t border-white/10 flex justify-end items-center gap-4 flex-shrink-0">
           {error && <p className="text-red-400 text-sm mr-auto">{error}</p>}
          <button onClick={onClose} className="px-5 py-2.5 font-semibold text-brand-text-muted hover:text-white">Cancel</button>
          <button onClick={handleSave} disabled={selectedClientIds.size === 0 || isSaving} className="px-6 py-2.5 bg-primary-action text-brand-dark font-bold rounded-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed w-48 text-center">
            {isSaving ? 'Saving...' : `Save Audience (${selectedClientIds.size})`}
          </button>
        </footer>
      </div>
    </div>
  );
};


// --- CORE UI COMPONENTS ---

/**
 * Displays a single piece of key intel with an optional icon, label, and value.
 */
const IntelStat: FC<{ icon?: ReactNode; label: string; value: string | number; className?: string }> = ({ icon, label, value, className }) => (
    <div className={`flex items-start gap-3 ${className}`}>
        {icon && <div className="mt-1 flex-shrink-0 text-brand-text-muted">{icon}</div>}
        <div>
            <p className="text-sm font-medium text-brand-text-muted">{label}</p>
            <p className="font-bold text-lg text-brand-text-main">{value}</p>
        </div>
    </div>
);

interface PersuasiveCommandCardProps {
    briefing: CampaignBriefing;
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void;
    // New prop: a single handler for both dismiss and send actions
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>;
    allClients: Client[];
}

/**
 * Represents a single "nudge" or campaign briefing card, allowing editing of the draft and audience, and initiating actions.
 */
const PersuasiveCommandCard: FC<PersuasiveCommandCardProps> = ({ briefing, onBriefingUpdate, onAction, allClients }) => {
    const config = NUDGE_TYPE_CONFIG[briefing.campaign_type] || NUDGE_TYPE_CONFIG.price_drop;
    const [draft, setDraft] = useState(briefing.edited_draft || briefing.original_draft || '');
    const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);

    // Update draft state when the briefing changes
    useEffect(() => {
        setDraft(briefing.edited_draft || briefing.original_draft || '');
    }, [briefing.id, briefing.original_draft, briefing.edited_draft]);

    // Extract image URL and key intel details from the briefing
    const imageUrl = useMemo(() => {
        const imageUrls = briefing.key_intel?.image_urls;
        return Array.isArray(imageUrls) && imageUrls.length > 0 ? imageUrls[0] : null;
    }, [briefing.key_intel]);
    const intel = briefing.key_intel || {};
    const price = intel.price ? `$${Number(intel.price).toLocaleString()}` : null;
    const beds = intel.bedrooms ? Number(intel.bedrooms) : null; // Safely convert to number or null
    const baths = intel.bathrooms ? Number(intel.bathrooms) : null; // Safely convert to number or null
    const sqft = intel.sqft ? `${Number(intel.sqft).toLocaleString()} sqft` : null;

    // Handles changes to the message draft textarea
    const handleDraftChange = (newDraft: string) => {
        setDraft(newDraft);
        onBriefingUpdate({ ...briefing, edited_draft: newDraft });
    };

    // Handles saving the audience changes from the modal
    const handleSaveAudience = async (newAudience: Client[]) => {
        const updatedMatchedAudience: MatchedClient[] = newAudience.map(c => ({
            client_id: c.id,
            client_name: c.full_name,
            match_score: 0, // Placeholder, as this might be AI-generated previously
            match_reason: 'Manually selected' // Indicate manual selection
        }));
        onBriefingUpdate({ ...briefing, matched_audience: updatedMatchedAudience });
    };

    return (
        <>
            {/* Modal for managing campaign audience */}
            <ManageAudienceModal
                isOpen={isAudienceModalOpen}
                onClose={() => setIsAudienceModalOpen(false)}
                onSave={handleSaveAudience}
                allClients={allClients}
                initialSelectedClientIds={new Set(briefing.matched_audience.map(c => c.client_id))}
            />
            <div className="absolute w-full h-full bg-brand-primary border border-white/10 rounded-xl overflow-hidden flex flex-col shadow-2xl">
                {/* Card Header */}
                <div className="flex-shrink-0 p-4 bg-black/30 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3"><span className={config.color}>{config.icon}</span><h3 className="font-bold text-lg text-brand-text-main">{briefing.headline}</h3></div>
                    {/* potential_commission has been removed from CampaignBriefing type in AppContext */}
                    {/* {briefing.potential_commission && (<div className="flex items-center gap-2 text-brand-accent px-3 py-1 bg-brand-accent/10 border border-brand-accent/20 rounded-md"><DollarSign size={16} /><span className="font-bold text-sm">~${briefing.potential_commission.toLocaleString()} GCI</span></div>)} */}
                </div>
                {/* Card Content: Key Intel & Audience/Draft */}
                <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-x-6 overflow-y-auto">
                    {/* Left Column: Property Image & Strategic Summary/Key Intel */}
                    <div className="p-5 space-y-5 border-r border-white/5">
                        {imageUrl && (<div className="relative w-full h-48 rounded-lg overflow-hidden"><Image src={imageUrl} alt={`Property at ${briefing.headline}`} layout="fill" objectFit="cover" className="bg-white/5"/></div>)}
                        <div className="space-y-1"><h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Target size={16}/>Strategic Summary</h4><p className="text-brand-text-main text-base">This is a key market event relevant to your clients.</p></div>
                        <div className="space-y-4 pt-2"><h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><ChevronsRight size={16}/>Key Intel</h4><div className="grid grid-cols-2 gap-4">{price && <IntelStat icon={<DollarSign size={20}/>} label="Price" value={price} />}{beds && <IntelStat icon={<BedDouble size={20}/>} label="Beds" value={beds} />}{baths && <IntelStat icon={<Bath size={20}/>} label="Baths" value={baths} />}{sqft && <IntelStat label="SqFt" value={sqft} />}</div></div>
                    </div>
                    {/* Right Column: Audience Management & Draft Message */}
                    <div className="p-5 space-y-5 flex flex-col">
                        <div>
                            <button onClick={() => setIsAudienceModalOpen(true)} className="w-full flex items-center justify-center gap-2 p-2 text-sm font-semibold text-brand-text-muted bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:text-brand-text-main transition-colors mb-3"><Users size={16}/>Manage Audience</button>
                            <div className="space-y-3 max-h-40 overflow-y-auto pr-2">
                                {/* Display matched audience clients */}
                                {briefing.matched_audience.map(client => (<div key={client.client_id}><p className="font-semibold text-brand-text-main text-base">{client.client_name}</p><p className={`text-sm ${config.color} flex items-center gap-1.5`}><Check size={14}/>{client.match_reason}</p></div>))}
                            </div>
                        </div>
                        <div className="flex-grow flex flex-col">
                            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2 mb-3"><Edit size={16}/>Draft Message</h4>
                            <textarea value={draft} onChange={(e) => handleDraftChange(e.target.value)} className="w-full flex-grow bg-brand-dark border border-white/10 rounded-md focus:ring-2 focus:ring-primary-action text-brand-text-main text-base p-3 resize-none"/>
                        </div>
                    </div>
                </div>
                {/* Card Footer: Action Buttons */}
                <div className="flex-shrink-0 p-3 bg-black/30 border-t border-white/10 grid grid-cols-2 gap-3">
                    {/* Dismiss Nudge button, calls onAction with 'dismiss' */}
                    <button onClick={() => onAction(briefing, 'dismiss')} className="p-3 bg-white/5 border border-white/10 text-brand-text-main rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-white/10 hover:border-white/20 transition-all duration-200"><X size={18} /> Dismiss Nudge</button>
                    {/* Send Nudge button, calls onAction with 'send' */}
                    <button onClick={() => onAction(briefing, 'send')} className="p-3 text-brand-dark rounded-lg font-bold flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(32,213,179,0.4)] hover:scale-[1.03] transition-all duration-200" style={{ backgroundColor: BRAND_ACCENT_COLOR }}><Send size={18} /> Send to {briefing.matched_audience.length} Client(s)</button>
                </div>
            </div>
        </>
    );
};

interface ActionDeckProps {
    briefings: CampaignBriefing[];
    onClose: () => void;
    // Consolidated action handler for dismiss and send
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>;
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void;
    allClients: Client[];
}

/**
 * A full-screen overlay component that displays a stack of `PersuasiveCommandCard`s,
 * allowing the user to action (send/dismiss) them one by one.
 */
const ActionDeck: FC<ActionDeckProps> = ({ briefings, onClose, onAction, onBriefingUpdate, allClients }) => {
    const [cardIndex, setCardIndex] = useState(0);

    // Handles the completion of an action (send or dismiss) for a briefing
    const handleActionComplete = async (briefing: CampaignBriefing, action: 'send' | 'dismiss') => {
        try {
            await onAction(briefing, action); // Execute the action via prop
            // Move to the next card or close the deck if no more cards
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
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-brand-dark/60 backdrop-blur-lg flex items-center justify-center z-50 p-4"
            >
                {/* Close button for the deck */}
                <button onClick={onClose} className="absolute top-4 right-4 text-brand-text-muted hover:text-brand-text-main transition-colors z-50"><X size={32}/></button>
                {/* Card counter */}
                <div className="absolute top-5 left-5 text-sm font-medium text-brand-text-muted z-50">{cardIndex + 1} of {briefings.length}</div>
                <div className="relative w-full max-w-4xl h-[90vh] max-h-[750px]">
                    <AnimatePresence mode="wait">
                        {/* Render the current card with animation */}
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
                                    onAction={handleActionComplete} // Pass the consolidated handler
                                    allClients={allClients}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

interface GroupCardProps {
    title: string;
    count: number;
    config: { color: string };
    onClick: () => void;
}

/**
 * A card component representing a group of opportunities/nudges,
 * typically displayed on the main dashboard.
 */
const GroupCard: FC<GroupCardProps> = ({ title, count, config, onClick }) => (
    <motion.button
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        onClick={onClick}
        className="w-full text-left p-4 bg-brand-dark/50 border border-white/5 rounded-lg flex items-center gap-4 transition-colors duration-200 hover:bg-brand-dark"
    >
        <div className="flex-grow">
            {/* Display title, extracting part after ': ' if present */}
            <h4 className="font-semibold text-base text-brand-text-main line-clamp-2">{title.split(': ').slice(1).join(': ')}</h4>
            <p className={`text-sm font-medium ${config.color}`}>{count} {count > 1 ? 'Opportunities' : 'Opportunity'}</p>
        </div>
        <ChevronRight size={20} className="flex-shrink-0 text-brand-text-muted" />
    </motion.button>
);

// --- MAIN PAGE COMPONENT ---
export default function NudgesPage() {
    // Connect to AppContext to get shared state and functions
    const { nudges, clients, api, loading, fetchDashboardData } = useAppContext();
    const [activeDeck, setActiveDeck] = useState<CampaignBriefing[] | null>(null);

    // Effect to load dashboard data when component mounts or dependencies change
    // This ensures data is fetched if not already present or if 'loading' state implies a need to fetch.
    useEffect(() => {
        if (!loading && nudges.length === 0) {
            fetchDashboardData();
        }
    }, [loading, nudges, fetchDashboardData]);

    /**
     * Handles either dismissing or sending a nudge.
     * Uses the API client from AppContext to make requests.
     * After any action, it refetches all dashboard data to ensure UI is in sync.
     * @param {CampaignBriefing} briefing - The briefing to action.
     * @param {'dismiss' | 'send'} action - The type of action to perform.
     */
    const handleAction = async (briefing: CampaignBriefing, action: 'dismiss' | 'send') => {
        try {
            if (action === 'send') {
                // Update briefing status to 'approved' and include edited draft and matched audience
                await api.put(`/api/campaigns/${briefing.id}`, {
                    edited_draft: briefing.edited_draft,
                    matched_audience: briefing.matched_audience,
                    status: 'approved'
                });
                // Trigger the send action
                await api.post(`/api/campaigns/${briefing.id}/send`, {});
            } else { // 'dismiss' action
                // Update briefing status to 'dismissed'
                await api.put(`/api/campaigns/${briefing.id}`, { status: 'dismissed' });
            }
            // After any action, refetch all data to ensure the UI is in sync
            await fetchDashboardData();
            // Close the active deck after an action is completed
            setActiveDeck(null);
        } catch (error) {
            console.error(`Failed to ${action} nudge:`, error);
            alert(`Error: Could not ${action} the nudge.`);
        }
    };

    /**
     * Handles updating a specific briefing within the currently active deck.
     * This is crucial for real-time draft and audience changes within the ActionDeck.
     * @param {CampaignBriefing} updatedBriefing - The briefing with updated details.
     */
    const handleBriefingUpdate = (updatedBriefing: CampaignBriefing) => {
        // This will update the local state for the active deck immediately
        // and the AppContext will eventually reflect this when fetchDashboardData is called after an action.
        if (activeDeck) {
            setActiveDeck(prevDeck => prevDeck?.map(b => b.id === updatedBriefing.id ? updatedBriefing : b) || null);
        }
    };

    // Memoized grouping of nudges by campaign type for display
    const groupedByEventType = useMemo(() =>
        nudges.reduce((acc, briefing) => ({
            ...acc,
            [briefing.campaign_type]: [...(acc[briefing.campaign_type] || []), briefing]
        }), {} as Record<string, CampaignBriefing[]>) // Explicitly type the accumulator for TypeScript
    , [nudges]);

    // Function to group briefings by headline within each event type
    const groupBriefingsByHeadline = (groupBriefings: CampaignBriefing[]) =>
        groupBriefings.reduce((acc, briefing) => ({
            ...acc,
            [briefing.headline]: [...(acc[briefing.headline] || []), briefing]
        }), {} as Record<string, CampaignBriefing[]>); // Explicitly type the accumulator for TypeScript

    // Animation variants for Framer Motion
    const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.08 } } };
    const columnVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

    return (
        <>
            {/* ActionDeck component, rendered conditionally when there's an active deck */}
            {activeDeck && (
                <ActionDeck
                    briefings={activeDeck}
                    onClose={() => setActiveDeck(null)}
                    onAction={handleAction} // Pass the new consolidated action handler
                    onBriefingUpdate={handleBriefingUpdate}
                    allClients={clients} // Pass clients from AppContext
                />
            )}
            <div className="min-h-screen bg-brand-dark text-brand-text-main font-sans">
                <main className="max-w-screen-xl mx-auto p-6 sm:p-8">
                    {/* Page Header */}
                    <header className="mb-12">
                        <h1 className="text-4xl sm:text-5xl font-bold text-brand-white tracking-tight">AI Opportunities</h1>
                        <p className="text-brand-text-muted mt-2 text-lg">Your AI co-pilot has identified the following revenue opportunities.</p>
                    </header>
                    {/* Loading state display */}
                    {loading && <div className="text-center py-20 text-brand-text-muted">Loading...</div>}
                    {/* Empty state display */}
                    {!loading && nudges.length === 0 && (
                        <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
                            <BrainCircuit className="mx-auto h-16 w-16 text-brand-text-muted" />
                            <h3 className="mt-4 text-xl font-medium text-brand-white">All Clear</h3>
                            <p className="mt-1 text-base text-brand-text-muted">The AI is watching the market. Check back soon.</p>
                        </div>
                    )}
                    {/* Display opportunities when loaded and available */}
                    {!loading && nudges.length > 0 && (
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
                                                <GroupCard
                                                    key={headline}
                                                    title={headline}
                                                    count={groupBriefings.length}
                                                    config={config}
                                                    onClick={() => setActiveDeck(groupBriefings)}
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