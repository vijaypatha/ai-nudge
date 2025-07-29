// frontend/components/nudges/ActionDeck.tsx

'use client';

import { useState, useEffect, useMemo, FC, ReactNode } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { CampaignBriefing as CampaignBriefingType, Client, MatchedClient } from '@/context/AppContext';
import { ManageAudienceModal } from '@/components/modals/ManageAudienceModal';
import { DisplayConfig } from './OpportunityNudgesView';
import {
    User as UserIcon, Sparkles, Send, X, Users, Home, TrendingUp, RotateCcw,
    TimerOff, CalendarPlus, Archive, Edit, DollarSign, Target, Check, ChevronsRight,
    BedDouble, Bath, ArrowLeftCircle, ArrowRightCircle, Play, ExternalLink,
    MessageSquare, Brain, Mic, Volume2, Newspaper, Building
} from 'lucide-react';

interface CampaignBriefing extends CampaignBriefingType {
    created_at: string;
    updated_at: string;
}

const ICONS: Record<string, ReactNode> = {
    Home: <Home size={20} />,
    Sparkles: <Sparkles size={20} />,
    TrendingUp: <TrendingUp size={20} />,
    RotateCcw: <RotateCcw size={20} />,
    TimerOff: <TimerOff size={20} />,
    CalendarPlus: <CalendarPlus size={20} />,
    Archive: <Archive size={20} />,
    UserIcon: <UserIcon size={20} />,
    Default: <Sparkles size={20} />,
};

const BRAND_ACCENT_COLOR = '#20D5B3';

const ScoreCircle: FC<{ score: number }> = ({ score }) => {
    const radius = 18;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color = score > 80 ? '#20D5B3' : score > 60 ? '#FBBF24' : '#4ADE80';
    return (<div className="relative flex-shrink-0 flex items-center justify-center w-12 h-12"><svg className="w-full h-full" viewBox="0 0 44 44"><circle className="text-white/5" strokeWidth="4" stroke="currentColor" fill="transparent" r={radius} cx="22" cy="22" /><motion.circle initial={{ strokeDashoffset: circumference }} animate={{ strokeDashoffset: offset }} transition={{ duration: 0.8, ease: "easeOut" }} strokeWidth="4" strokeDasharray={circumference} strokeLinecap="round" stroke={color} fill="transparent" r={radius} cx="22" cy="22" transform="rotate(-90 22 22)" /></svg><span className="absolute text-sm font-bold text-brand-text-main">{score}</span></div>);
};

const MatchReasonTag: FC<{ reason: string }> = ({ reason }) => {
    const isNewInfo = reason.startsWith('✅');
    const isHotLead = reason.startsWith('🔥');
    
    const icon = isNewInfo ? '✅' : isHotLead ? '🔥' : '✨';
    const text = reason.replace(/^[🔥✅✨]\s*/, '');
    const bgColor = isNewInfo ? 'bg-primary-action/20' : 'bg-white/5';
    const textColor = isNewInfo ? 'text-primary-action' : 'text-brand-text-muted';

    return (
        <div className={`flex items-center gap-1.5 text-xs font-medium ${bgColor} py-1 px-2.5 rounded-full`}>
            <span>{icon}</span>
            <span className={textColor}>{text}</span>
        </div>
    );
};

const ContentPreview: FC<{ intel: any }> = ({ intel }) => {
    const previewData = intel?.content_preview;
    if (!previewData || (!previewData.url && !previewData.image_url && !previewData.title)) {
        return null;
    }
    const { content_type, url, image_url, title, description, details } = previewData;
    const isYouTube = content_type === 'youtube';
    const isVideo = content_type === 'video';
    const isProperty = content_type === 'property';
    const renderDetail = (label: string, value: any, icon: ReactNode) => {
        if (!value) return null;
        return (
            <span className="bg-white/10 text-brand-text-muted px-2 py-1 rounded flex items-center gap-1.5">
                {icon} {label}: {value}
            </span>
        );
    };

    return (
        <div className="space-y-3">
            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2">
                <ChevronsRight size={16} /> Key Intel
            </h4>
            <div className="relative w-full h-48 rounded-lg overflow-hidden bg-white/5 border border-white/10 group">
                {image_url ? (
                    <Image src={image_url} alt={title || 'Content Preview'} layout="fill" objectFit="cover" className="bg-white/5" />
                ) : (
                    <div className="w-full h-full flex items-center justify-center bg-brand-dark">
                        <Newspaper size={48} className="text-brand-text-muted" />
                    </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                
                {(isVideo || isYouTube) && (
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="bg-black/50 rounded-full p-4"><Play size={32} className="text-white" /></div>
                    </div>
                )}
                
                <div className="absolute top-2 left-2">
                    <span className="bg-black/70 text-white text-xs px-2 py-1 rounded-full capitalize flex items-center gap-1">
                        {isProperty ? <Building size={12} /> : <Newspaper size={12} />}
                        {content_type}
                    </span>
                </div>
                
                {url && (
                    <a href={url} target="_blank" rel="noopener noreferrer" className="absolute top-2 right-2 bg-black/70 text-white p-2 rounded-full hover:bg-black/90 transition-colors" title="Open in new tab">
                        <ExternalLink size={16} />
                    </a>
                )}

                <div className="absolute bottom-3 left-3 right-3">
                    {title && <h5 className="font-bold text-white text-base drop-shadow-md">{title}</h5>}
                </div>
            </div>
            
            <div className="space-y-2">
                {description && <p className="text-brand-text-muted text-sm line-clamp-3">{description}</p>}
                
                {isProperty && details && (
                    <div className="flex flex-wrap gap-2 text-xs">
                        {renderDetail("Price", details.price?.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }), '💰')}
                        {renderDetail("Beds", details.bedrooms, '🛏️')}
                        {renderDetail("Baths", details.bathrooms, '🚿')}
                        {renderDetail("SqFt", details.sqft?.toLocaleString(), '📏')}
                    </div>
                )}
            </div>
        </div>
    );
};

const ToneMatchingIndicator: FC<{ intel: any }> = ({ intel }) => {
    const styleMatchScore = intel['style_match_score'] || 85;
    const toneIndicators = intel['tone_indicators'] || ['Professional', 'Friendly'];
    
    return (
        <div className="space-y-3">
            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2">
                <Brain size={16} /> Voice Matching
            </h4>
            <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-green-400 to-blue-500 flex items-center justify-center">
                        <Mic size={20} className="text-white" />
                    </div>
                </div>
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-brand-text-main">Style Match</span>
                        <span className="text-xs font-bold text-green-400">{styleMatchScore}%</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {toneIndicators.map((indicator: string, index: number) => (
                            <span key={index} className="text-xs bg-white/10 text-brand-text-muted px-2 py-1 rounded-full">
                                {indicator}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

interface PersuasiveCommandCardProps {
    briefing: CampaignBriefing;
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void;
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>;
    displayConfig: DisplayConfig;
}

const PersuasiveCommandCard: FC<PersuasiveCommandCardProps> = ({ briefing, onBriefingUpdate, onAction, displayConfig }) => {
    const config = displayConfig[briefing.campaign_type] || { icon: 'Default', color: 'text-primary-action', title: 'Nudge' };
    const icon = ICONS[config.icon] || ICONS.Default;
    
    const [draft, setDraft] = useState(briefing.edited_draft || briefing.original_draft || '');
    const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);
    const matchedAudience = useMemo(() => briefing.matched_audience ?? [], [briefing.matched_audience]);

    useEffect(() => { setDraft(briefing.edited_draft || briefing.original_draft || ''); }, [briefing.id, briefing.original_draft, briefing.edited_draft]);

    const intel = briefing.key_intel || {};
    const strategicContext = intel['strategic_context'] || 'This is a key market event relevant to your clients.';
    const timingRationale = intel['timing_rationale'] || 'Optimal timing for client engagement.';
    const triggerSource = intel['trigger_source'] || 'AI Analysis';

    const wasRescored = useMemo(() => {
        if (!briefing.created_at || !briefing.updated_at) return false;
        const created = new Date(briefing.created_at).getTime();
        const updated = new Date(briefing.updated_at).getTime();
        return (updated - created) > 60000; 
    }, [briefing.created_at, briefing.updated_at]);

    const handleDraftChange = (newDraft: string) => { setDraft(newDraft); onBriefingUpdate({ ...briefing, edited_draft: newDraft }); };
    
    const handleSaveAudience = async (newAudience: Client[]) => {
        const updatedMatchedAudience: MatchedClient[] = newAudience.map(c => ({ client_id: c.id, client_name: c.full_name, match_score: 0, match_reasons: ['Manually Added'] }));
        onBriefingUpdate({ ...briefing, matched_audience: updatedMatchedAudience });
    };

    return (
        <>
            <ManageAudienceModal isOpen={isAudienceModalOpen} onClose={() => setIsAudienceModalOpen(false)} onSave={handleSaveAudience} initialSelectedClientIds={new Set(matchedAudience.map(c => c.client_id))} />
            <div className="absolute w-full h-full bg-brand-primary border border-white/10 rounded-xl overflow-hidden flex flex-col shadow-2xl">
                <div className="flex-shrink-0 p-4 bg-black/30 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className={config.color}>{icon}</span>
                        <h3 className="font-bold text-lg text-brand-text-main">{briefing.headline}</h3>
                        {wasRescored && (
                            <span className="flex items-center gap-1.5 bg-primary-action/20 text-primary-action text-xs font-bold px-2 py-1 rounded-full animate-in fade-in-0 zoom-in-95">
                                <Sparkles size={12}/> Re-scored
                            </span>
                        )}
                    </div>
                    <div className="text-xs text-brand-text-muted bg-white/10 px-2 py-1 rounded-full">{triggerSource}</div>
                </div>
                
                <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-x-6 overflow-y-auto">
                    {/* Left Panel - Strategic Context & Preview */}
                    <div className="p-5 space-y-6 border-r border-white/5">
                        <ContentPreview intel={intel} />
                        
                        <div className="space-y-3">
                            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2"><Target size={16}/> Strategic Context</h4>
                            <div className="space-y-2"><p className="text-brand-text-main text-base">{strategicContext}</p><p className="text-sm text-brand-text-muted">{timingRationale}</p></div>
                        </div>
                        
                        <ToneMatchingIndicator intel={intel} />
                    </div>
                    
                    {/* Right Panel - Audience & Message */}
                    <div className="p-5 space-y-5 flex flex-col">
                        <div>
                            <button onClick={() => setIsAudienceModalOpen(true)} className="w-full flex items-center justify-center gap-2 p-2 text-sm font-semibold text-brand-text-muted bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:text-brand-text-main transition-colors mb-4">
                                <Users size={16}/> Manage Audience ({matchedAudience.length})
                            </button>
                            <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
                                {matchedAudience.map((client, index) => (
                                    <div key={client.client_id} className="p-3 bg-white/[.03] border border-white/5 rounded-lg">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <ScoreCircle score={client.match_score} />
                                                <div>
                                                    <p className="font-semibold text-brand-text-main text-base">{client.client_name}</p>
                                                    {index === 0 && <p className="text-xs font-bold text-amber-400">Top Match</p>}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-2 mt-2 pl-[60px]">
                                            {client.match_reasons?.map(reason => <MatchReasonTag key={reason} reason={reason} />)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        <div className="flex-grow flex flex-col mt-4">
                            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2 mb-2"><Edit size={16}/> Draft Message</h4>
                            <textarea value={draft} onChange={(e) => handleDraftChange(e.target.value)} className="w-full flex-grow bg-brand-dark border border-white/10 rounded-md focus:ring-2 focus:ring-primary-action text-brand-text-main text-base p-3 resize-none" placeholder="Your personalized message will appear here..."/>
                        </div>
                    </div>
                </div>
                
                <div className="flex-shrink-0 p-3 bg-black/30 border-t border-white/10 grid grid-cols-2 gap-3">
                    <button onClick={() => onAction(briefing, 'dismiss')} className="p-3 bg-white/5 border border-white/10 text-brand-text-main rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-white/10 hover:border-white/20 transition-all duration-200"><X size={18} /> Dismiss Nudge</button>
                    <button onClick={() => onAction(briefing, 'send')} className="p-3 text-brand-dark rounded-lg font-bold flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(32,213,179,0.4)] hover:scale-[1.03] transition-all duration-200" style={{ backgroundColor: BRAND_ACCENT_COLOR }}><Send size={18} /> Send to {matchedAudience.length} Client(s)</button>
                </div>
            </div>
        </>
    );
};


interface ActionDeckProps { 
    briefings: CampaignBriefing[]; 
    onClose: () => void; 
    onAction: (briefing: CampaignBriefing, action: 'dismiss' | 'send') => Promise<void>; 
    onBriefingUpdate: (updatedBriefing: CampaignBriefing) => void; 
    displayConfig: DisplayConfig;
}

export const ActionDeck: FC<ActionDeckProps> = ({ briefings, onClose, onAction, onBriefingUpdate, displayConfig }) => {
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
                {briefings.length > 1 && (
                    <>
                        <button onClick={() => setCardIndex(prev => (prev > 0 ? prev - 1 : briefings.length - 1))} className="absolute left-4 md:left-10 top-1/2 -translate-y-1/2 z-50 text-white/50 hover:text-white transition-colors"><ArrowLeftCircle size={36} /></button>
                        <button onClick={() => setCardIndex(prev => (prev < briefings.length - 1 ? prev + 1 : 0))} className="absolute right-4 md:right-10 top-1/2 -translate-y-1/2 z-50 text-white/50 hover:text-white transition-colors"><ArrowRightCircle size={36} /></button>
                    </>
                )}
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
                                    displayConfig={displayConfig}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};