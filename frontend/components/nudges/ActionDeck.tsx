// frontend/components/nudges/ActionDeck.tsx
// --- FINAL, PRODUCTION-READY VERSION ---

'use client';

import { useState, FC, ReactNode, useEffect } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { CampaignBriefing as CampaignBriefingType, Client, MatchedClient } from '@/context/AppContext';
import { ManageAudienceModal } from '@/components/modals/ManageAudienceModal';
import { DisplayConfig } from './OpportunityNudgesView';
import { PhotoGalleryModal } from '@/components/modals/PhotoGalleryModal';
import { RelationshipTimeline } from './RelationshipTimeline';
import {
    User as UserIcon, Sparkles, Send, X, Users, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, Edit, ArrowLeftCircle,
    ArrowRightCircle, Brain, Mic, ChevronsRight, ImageIcon, BrainCircuit, BookOpen
} from 'lucide-react';

// The full briefing type returned by the /clients/{id}/nudges endpoint
interface ClientNudge extends CampaignBriefingType {
    campaign_id: string;
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

const ICONS: Record<string, ReactNode> = {
    Home: <Home size={20} />, Sparkles: <Sparkles size={20} />, TrendingUp: <TrendingUp size={20} />,
    RotateCcw: <RotateCcw size={20} />, TimerOff: <TimerOff size={20} />, CalendarPlus: <CalendarPlus size={20} />,
    Archive: <Archive size={20} />, UserIcon: <UserIcon size={20} />, Default: <Sparkles size={20} />,
};

const BRAND_ACCENT_COLOR = '#20D5B3';

// --- UI Sub-Components ---

const ScoreCircle: FC<{ score: number }> = ({ score }) => {
    const radius = 18;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color = score > 70 ? '#20D5B3' : score > 40 ? '#FBBF24' : '#FB7185';
    return (<div className="relative flex-shrink-0 flex items-center justify-center w-12 h-12"><svg className="w-full h-full" viewBox="0 0 44 44"><circle className="text-white/5" strokeWidth="4" stroke="currentColor" fill="transparent" r={radius} cx="22" cy="22" /><motion.circle initial={{ strokeDashoffset: circumference }} animate={{ strokeDashoffset: offset }} transition={{ duration: 0.8, ease: "easeOut" }} strokeWidth="4" strokeDasharray={circumference} strokeLinecap="round" stroke={color} fill="transparent" r={radius} cx="22" cy="22" transform="rotate(-90 22 22)" /></svg><span className="absolute text-sm font-bold text-brand-text-main">{score}</span></div>);
};

const MatchReasonTag: FC<{ reason: string }> = ({ reason }) => {
    const icon = reason.startsWith('✅') ? '✅' : reason.startsWith('🔥') ? '🔥' : '✨';
    const text = reason.replace(/^[🔥✅✨]\s*/, '');
    return (<div className={`flex items-center gap-1.5 text-xs font-medium bg-white/5 py-1 px-2.5 rounded-full`}><span className="text-primary-action">{icon}</span><span className="text-brand-text-muted">{text}</span></div>);
};

const ResourceCard: FC<{ resource: ClientNudge['resource'], briefing: ClientNudge }> = ({ resource, briefing }) => {
    const contentPreview = briefing.key_intel?.content_preview || {};
    const [showPhotoGallery, setShowPhotoGallery] = useState(false);
    const [imageError, setImageError] = useState(false);
    const isContentNudge = briefing.campaign_type === 'content_suggestion' || briefing.campaign_type === 'content_recommendation';

    // Centralized data extraction from the most reliable source: key_intel.content_preview
    const {
        title: previewTitle,
        image_url: imageUrl,
        photo_gallery: galleryPhotos = [],
        photo_count: photoCount = 0,
        details = {}
    } = contentPreview;

    const {
        price,
        bedrooms,
        bathrooms,
        sqft
    } = details as { price?: any, bedrooms?: any, bathrooms?: any, sqft?: any };

    // Fallback for address: preview title -> resource.address -> parse headline
    const displayAddress = previewTitle || resource.address || briefing.headline.replace('New Listing: ', '');

    const handleImageError = () => {
        setImageError(true);
        console.warn('Failed to load image:', imageUrl);
    };

    if (isContentNudge) {
        const { url, content_type, title } = briefing.resource?.attributes || {};
        return (
            <div className="space-y-3">
                <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><BookOpen size={16} /> Content Resource</h4>
                <div className="relative w-full h-48 rounded-lg overflow-hidden bg-white/5 border border-white/10 group flex items-center justify-center">
                    <BookOpen size={48} className="text-brand-text-muted" />
                    <div className="absolute bottom-3 left-3 right-3 p-2 bg-black/40 rounded">
                        <h5 className="font-bold text-white text-base drop-shadow-md truncate">{title}</h5>
                    </div>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                    <span className="bg-white/10 text-brand-text-muted px-2 py-1 rounded">Type: {content_type}</span>
                    {url && <button onClick={() => window.open(url, '_blank')} className="bg-white/10 text-brand-text-muted px-2 py-1 rounded hover:bg-white/20">🔗 Preview Content</button>}
                </div>
            </div>
        );
    }

    const renderDetail = (label: string, value: any) => {
        if (!value && value !== 0) return null;
        const formattedValue = label === 'Price' && typeof value === 'number' ? `$${value.toLocaleString('en-US')}` : value?.toLocaleString();
        return (<span className="bg-black/30 text-white/80 text-xs font-semibold px-2.5 py-1 rounded">{label}: {formattedValue}</span>);
    };

    return (
        <div className="space-y-3">
            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Home size={16} /> Property</h4>
            <div className="relative w-full h-48 rounded-lg overflow-hidden bg-brand-dark border border-white/10 group">
                {imageUrl && !imageError ? (
                    <Image
                        src={imageUrl}
                        alt={displayAddress}
                        layout="fill"
                        objectFit="cover"
                        unoptimized
                        onError={handleImageError}
                    />
                ) : (
                    <div className="w-full h-full flex flex-col justify-between items-start p-4 bg-white/5">
                        <ImageIcon size={32} className="text-brand-text-muted/50" />
                        <div className="w-full">
                            <h5 className="font-bold text-white text-base drop-shadow-md">{displayAddress}</h5>
                            <div className="flex flex-wrap gap-2 text-xs mt-2">
                                {renderDetail("Price", price)}
                                {renderDetail("Beds", bedrooms)}
                                {renderDetail("Baths", bathrooms)}
                                {renderDetail("SqFt", sqft)}
                            </div>
                        </div>
                    </div>
                )}
                {photoCount > 1 && (<button onClick={() => setShowPhotoGallery(true)} className="absolute top-2 right-2 bg-black/70 text-white p-2 rounded-full hover:bg-black/90" title={`View all ${photoCount} photos`}><ImageIcon size={16} /></button>)}
            </div>
            {showPhotoGallery && <PhotoGalleryModal photos={galleryPhotos} onClose={() => setShowPhotoGallery(false)} />}
        </div>
    );
};

const ToneMatchingIndicator: FC = () => (
    <div className="space-y-3">
        <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Brain size={16} /> Voice Matching</h4>
        <div className="flex items-center gap-3"><div className="flex-shrink-0"><div className="w-12 h-12 rounded-full bg-gradient-to-r from-green-400 to-blue-500 flex items-center justify-center"><Mic size={20} className="text-white" /></div></div><div className="flex-1"><div className="flex items-center gap-2 mb-1"><span className="text-sm font-medium text-brand-text-main">Style Match</span><span className="text-xs font-bold text-green-400">85%</span></div><div className="flex flex-wrap gap-1"><span className="text-xs bg-white/10 text-brand-text-muted px-2 py-1 rounded-full">Professional</span><span className="text-xs bg-white/10 text-brand-text-muted px-2 py-1 rounded-full">Friendly</span></div></div></div>
    </div>
);


interface PersuasiveCommandCardProps {
    briefing: ClientNudge;
    onDraftChange: (newDraft: string) => void;
    onAudienceUpdate: (newAudience: Client[]) => void;
    onAction: (action: 'dismiss' | 'send') => Promise<void>;
    displayConfig: DisplayConfig;
}

const PersuasiveCommandCard: FC<PersuasiveCommandCardProps> = ({ briefing, onDraftChange, onAudienceUpdate, onAction, displayConfig }) => {
    const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);

    const config = displayConfig[briefing.campaign_type] || { icon: 'Default', color: 'text-primary-action', title: 'Nudge' };
    const icon = ICONS[config.icon] || ICONS.Default;
    const draft = briefing.edited_draft ?? briefing.original_draft ?? '';
    const matchedAudience = briefing.matched_audience ?? [];

    const generateLinks = () => {
        const contentPreview = briefing.key_intel?.content_preview || {};
        const photoUrls = contentPreview.photo_gallery || [];

        // Check for content-based nudge first
        if ((briefing.campaign_type === 'content_suggestion' || briefing.campaign_type === 'content_recommendation')) {
            const contentUrl = contentPreview.url;
            const contentType = contentPreview.content_type;

            if (contentUrl) {
                return `\n\n🔗 View ${contentType || 'Content'}: ${contentUrl}`;
            }
        }

        if (photoUrls.length === 0) return '';

        if (photoUrls.length === 1) {
            return `\n\n📸 View photos: ${photoUrls[0]}`;
        } else {
            const maxPhotos = 3;
            const photosToShow = photoUrls.slice(0, maxPhotos);
            const photoLinks = photosToShow.map((url: string, index: number) => `📸 Photo ${index + 1}: ${url}`).join('\n');

            if (photoUrls.length <= maxPhotos) {
                return `\n\n📸 View all ${photoUrls.length} photos:\n${photoLinks}`;
            } else {
                return `\n\n📸 View first 3 of ${photoUrls.length} photos:\n${photoLinks}`;
            }
        }
    };

    const getDisplayText = () => {
        const links = generateLinks();
        const hasLinks = draft.includes('📸') || draft.includes('🔗') || draft.includes('View photos') || draft.includes('View ');

        if (links && !hasLinks) {
            return draft + links;
        }
        return draft;
    };

    const handleSaveAudience = async (newAudience: Client[]) => {
      onAudienceUpdate(newAudience);
      setIsAudienceModalOpen(false);
    }

    return (
        <>
            <ManageAudienceModal isOpen={isAudienceModalOpen} onClose={() => setIsAudienceModalOpen(false)} onSave={handleSaveAudience} initialSelectedClientIds={new Set(matchedAudience.map(c => c.client_id))} />
            <div className="absolute w-full h-full bg-brand-primary border border-white/10 rounded-xl overflow-hidden flex flex-col shadow-2xl">
                <header className="flex-shrink-0 p-4 bg-black/30 border-b border-white/10 flex items-center justify-between"><div className="flex items-center gap-3"><span className={config.color}>{icon}</span><h3 className="font-bold text-lg text-brand-text-main">{briefing.headline}</h3></div></header>
                <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-x-6 overflow-y-auto">
                    {/* Left Column */}
                    <div className="p-5 space-y-6 border-r border-white/5">
                        <ResourceCard resource={briefing.resource} briefing={briefing} />
                        <RelationshipTimeline clientId={briefing.matched_audience[0]?.client_id} />
                        <div className="space-y-3">
                            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><ChevronsRight size={16}/> Strategic Context</h4>
                            <p className="text-brand-text-main text-base">
                                {(briefing.campaign_type === 'content_suggestion' || briefing.campaign_type === 'content_recommendation')
                                    ? "This content resource matches your client's interests and needs."
                                    : "This is a key market event relevant to your clients."
                                }
                            </p>
                        </div>
                        <ToneMatchingIndicator />
                    </div>
                    {/* Right Column */}
                    <div className="p-5 space-y-5 flex flex-col">
                        <div>
                            <button onClick={() => setIsAudienceModalOpen(true)} className="w-full flex items-center justify-center gap-2 p-2 text-sm font-semibold text-brand-text-muted bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:text-brand-text-main transition-colors mb-4"><Users size={16}/> Manage Audience ({matchedAudience.length})</button>
                            <div className="space-y-3 max-h-48 overflow-y-auto pr-2">{matchedAudience.map((client) => (<div key={client.client_id} className="p-3 bg-white/[.03] border border-white/5 rounded-lg"><div className="flex items-center justify-between"><div className="flex items-center gap-3"><ScoreCircle score={client.match_score} /><div><p className="font-semibold text-brand-text-main text-base">{client.client_name}</p></div></div></div>{client.match_reasons && client.match_reasons.length > 0 && (<div className="flex flex-wrap items-center gap-2 mt-2 pl-[60px]"><MatchReasonTag reason={client.match_reasons[0]} /></div>)}</div>))}</div>
                        </div>
                        <div className="flex-grow flex flex-col mt-4">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Edit size={16}/> Draft Message</h4>
                                {briefing.campaign_type === 'content_suggestion' && briefing.resource?.attributes?.url && (
                                    <button
                                        onClick={() => window.open(briefing.resource.attributes.url, '_blank')}
                                        className="text-xs bg-white/10 text-brand-text-muted px-2 py-1 rounded hover:bg-white/20 hover:text-brand-text-main transition-colors"
                                    >
                                        🔗 Preview Content
                                    </button>
                                )}
                            </div>
                            <textarea value={getDisplayText()} onChange={(e) => onDraftChange(e.target.value)} className="w-full flex-grow bg-brand-dark border border-white/10 rounded-md focus:ring-2 focus:ring-primary-action text-brand-text-main text-base p-3 resize-none" placeholder="Your personalized message will appear here..."/>
                        </div>
                    </div>
                </div>
                <footer className="flex-shrink-0 p-3 bg-black/30 border-t border-white/10 grid grid-cols-2 gap-3"><button onClick={() => onAction('dismiss')} className="p-3 bg-white/5 border border-white/10 text-brand-text-main rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-white/10 hover:border-white/20 transition-all duration-200"><X size={18} /> Dismiss Nudge</button><button onClick={() => onAction('send')} disabled={matchedAudience.length === 0} className="p-3 text-brand-dark rounded-lg font-bold flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(32,213,179,0.4)] hover:scale-[1.03] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed" style={{ backgroundColor: BRAND_ACCENT_COLOR }}><Send size={18} /> Send to {matchedAudience.length} Client(s)</button></footer>
            </div>
        </>
    );
};

interface ActionDeckProps {
    initialBriefings: ClientNudge[];
    initialClientId: string;
    initialClientName: string;
    onClose: () => void;
    onAction: (briefing: CampaignBriefingType, action: 'dismiss' | 'send') => Promise<void>;
    displayConfig: DisplayConfig;
}

export const ActionDeck: FC<ActionDeckProps> = ({ initialBriefings, initialClientId, initialClientName, onClose, onAction, displayConfig }) => {

    const [originalBriefings] = useState(initialBriefings);

    // Helper function to generate links for a briefing
    const generateLinksForBriefing = (briefing: ClientNudge) => {
        // Source data consistently from key_intel.content_preview
        const contentPreview = briefing.key_intel?.content_preview || {};

        // Check for content-based nudge first
        if ((briefing.campaign_type === 'content_suggestion' || briefing.campaign_type === 'content_recommendation') && contentPreview.url) {
            return `\n\n🔗 View ${contentPreview.content_type || 'Content'}: ${contentPreview.url}`;
        }

        // Fallback to property-based nudge (photos)
        const photoUrls = contentPreview.photo_gallery || [];

        if (photoUrls.length === 0) return '';

        if (photoUrls.length === 1) {
            return `\n\n📸 View photos: ${photoUrls[0]}`;
        } else {
            const maxPhotos = 3;
            const photosToShow = photoUrls.slice(0, maxPhotos);
            const photoLinks = photosToShow.map((url: string, index: number) => `📸 Photo ${index + 1}: ${url}`).join('\n');

            if (photoUrls.length <= maxPhotos) {
                return `\n\n📸 View all ${photoUrls.length} photos:\n${photoLinks}`;
            } else {
                return `\n\n📸 View first 3 of ${photoUrls.length} photos:\n${photoLinks}`;
            }
        }
    };

    const getInitialState = () => {
        return originalBriefings.map(briefing => {
            // Find the primary client in the original audience
            const primaryClient = briefing.matched_audience?.find(c => c.client_id === initialClientId);

            // Create a new audience with only the primary client
            const audience = primaryClient ? [primaryClient] : [{
                client_id: initialClientId,
                client_name: initialClientName,
                match_score: 75,
                match_reasons: ["Primary client for this context"]
            }];

            // Initialize edited_draft with content that includes links
            const baseDraft = briefing.edited_draft || briefing.original_draft || "";
            const links = generateLinksForBriefing(briefing);
            const initialDraft = links && !baseDraft.includes('📸') && !baseDraft.includes('🔗')
                ? baseDraft + links
                : baseDraft;

            return {
                ...briefing,
                matched_audience: audience,
                edited_draft: initialDraft
            };
        });
    };

    const [displayBriefings, setDisplayBriefings] = useState(getInitialState);
    const [cardIndex, setCardIndex] = useState(0);

    const currentDisplayBriefing = displayBriefings[cardIndex];

    const handleActionComplete = async (action: 'send' | 'dismiss') => {
        const briefingToSend = displayBriefings[cardIndex];
        await onAction(briefingToSend, action);

        const newDisplayBriefings = displayBriefings.filter(b => b.id !== briefingToSend.id);
        setDisplayBriefings(newDisplayBriefings);

        if (newDisplayBriefings.length === 0) {
            onClose();
        } else if (cardIndex >= newDisplayBriefings.length) {
            setCardIndex(newDisplayBriefings.length - 1);
        }
    };

    const handleDraftChange = (newDraft: string) => {
        const newBriefings = [...displayBriefings];
        newBriefings[cardIndex].edited_draft = newDraft;
        setDisplayBriefings(newBriefings);
    };

    const handleAudienceUpdate = (newAudience: Client[]) => {
        const originalFullAudience = originalBriefings.find(b => b.id === currentDisplayBriefing.id)?.matched_audience || [];

        const updatedAudience = newAudience.map(c => {
            const existingClientData = originalFullAudience.find(mc => mc.client_id === c.id);
            return {
                client_id: c.id,
                client_name: c.full_name,
                match_score: existingClientData?.match_score || 50,
                match_reasons: existingClientData?.match_reasons || ["Manually Added"]
            };
        });

        const newDisplayBriefings = [...displayBriefings];
        newDisplayBriefings[cardIndex].matched_audience = updatedAudience;
        setDisplayBriefings(newDisplayBriefings);
    };

    if (displayBriefings.length === 0 || !currentDisplayBriefing) {
        return (
             <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-brand-dark/60 backdrop-blur-lg flex items-center justify-center z-50 p-4">
                 <div className="text-center p-8 bg-brand-primary border border-white/10 rounded-xl">
                    <BrainCircuit className="mx-auto h-16 w-16 text-brand-text-muted" />
                    <h3 className="mt-4 text-xl font-medium text-brand-white">All Clear for {initialClientName}</h3>
                    <p className="mt-1 text-base text-brand-text-muted">No new opportunities at the moment.</p>
                    <button onClick={onClose} className="mt-6 px-4 py-2 text-sm font-semibold bg-white/10 rounded-md">Close</button>
                </div>
            </motion.div>
        );
    }

    return (
        <AnimatePresence>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-brand-dark/60 backdrop-blur-lg flex items-center justify-center z-50 p-4">
                <button onClick={onClose} className="absolute top-4 right-4 text-brand-text-muted hover:text-brand-text-main transition-colors z-50"><X size={32}/></button>
                <div className="absolute top-5 left-5 text-sm font-medium text-brand-text-muted z-50">{cardIndex + 1} of {displayBriefings.length}</div>
                {displayBriefings.length > 1 && (
                    <>
                        <button onClick={() => setCardIndex(prev => (prev > 0 ? prev - 1 : displayBriefings.length - 1))} className="absolute left-4 md:left-10 top-1/2 -translate-y-1/2 z-50 text-white/50 hover:text-white transition-colors"><ArrowLeftCircle size={36} /></button>
                        <button onClick={() => setCardIndex(prev => (prev < displayBriefings.length - 1 ? prev + 1 : 0))} className="absolute right-4 md:right-10 top-1/2 -translate-y-1/2 z-50 text-white/50 hover:text-white transition-colors"><ArrowRightCircle size={36} /></button>
                    </>
                )}
                <div className="relative w-full max-w-4xl h-[90vh] max-h-[750px]">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentDisplayBriefing.id}
                            initial={{ scale: 0.95, y: 50, opacity: 0 }}
                            animate={{ scale: 1, y: 0, opacity: 1 }}
                            exit={{ scale: 0.95, y: -50, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            className="absolute inset-0"
                        >
                            <PersuasiveCommandCard
                                briefing={currentDisplayBriefing}
                                onDraftChange={handleDraftChange}
                                onAudienceUpdate={handleAudienceUpdate}
                                onAction={(action) => handleActionComplete(action)}
                                displayConfig={displayConfig}
                            />
                        </motion.div>
                    </AnimatePresence>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};