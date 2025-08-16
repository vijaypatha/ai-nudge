// frontend/components/nudges/ActionDeck.tsx
'use client';

import { useState, FC, ReactNode, useEffect, useCallback } from 'react';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { useAppContext } from '@/context/AppContext';
import { DisplayConfig } from './OpportunityNudgesView';
import { Send, X, Users, Home, Edit, RefreshCw, Info } from 'lucide-react';

// --- Type Definitions ---
interface RenderedMatch {
    resource_id: string;
    resource_data: Record<string, any>;
    agent_commentary: string;
    score: number;
    reasons: string[];
}
interface RenderedBriefingResponse {
    id: string;
    campaign_type: string;
    headline: string;
    original_draft: string;
    key_intel: {
        curation_rationale?: string;
        [key: string]: any;
    };
    matched_audience: { client_id: string; client_name: string }[];
    top_matches_rendered: RenderedMatch[];
}
interface ActionDeckProps {
    briefingId: string;
    onClose: () => void;
    displayConfig: DisplayConfig;
}

// --- Sub-Component for displaying a single rendered match ---
const RenderedMatchCard: FC<{ match: RenderedMatch; onSave: (resourceId: string, newCommentary: string) => void; }> = ({ match, onSave }) => {
    const [commentary, setCommentary] = useState(match.agent_commentary);
    const primaryPhoto = match.resource_data?.Media?.find((p: any) => p.Order === 0)?.MediaURL || match.resource_data?.Media?.[0]?.MediaURL || '/placeholder.jpg';

    const handleSave = () => {
        if (commentary !== match.agent_commentary) {
            onSave(match.resource_id, commentary);
        }
    };

    return (
        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-3">
            <div className="flex gap-4">
                <div className="relative w-24 h-24 rounded-md overflow-hidden flex-shrink-0">
                    <Image src={primaryPhoto} layout="fill" objectFit="cover" alt="Property" unoptimized/>
                </div>
                <div className="flex-1">
                    <p className="font-bold text-white">{match.resource_data.UnparsedAddress || "Address not available"}</p>
                    <p className="text-sm text-gray-300">{match.resource_data.City}, {match.resource_data.StateOrProvince}</p>
                    <p className="text-lg font-semibold text-green-400 mt-1">${(match.resource_data.ListPrice || 0).toLocaleString()}</p>
                </div>
            </div>
            <div>
                <h5 className="text-xs font-semibold text-gray-400 mb-1">Agent's Note</h5>
                <textarea 
                    value={commentary} 
                    onChange={(e) => setCommentary(e.target.value)}
                    onBlur={handleSave} // Save when the user clicks away
                    className="w-full bg-black/20 p-2 rounded-md border border-gray-700/50 text-sm text-gray-200 resize-none focus:ring-2 focus:ring-indigo-500"
                    rows={4}
                />
            </div>
        </div>
    );
};


// --- Main ActionDeck Component ---
export const ActionDeck: FC<ActionDeckProps> = ({ briefingId, onClose, displayConfig }) => {
    const { api } = useAppContext();
    const [briefingData, setBriefingData] = useState<RenderedBriefingResponse | null>(null);
    const [editedDraft, setEditedDraft] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);

    const fetchData = useCallback(async (id: string) => {
        setIsLoading(true);
        try {
            const data: RenderedBriefingResponse = await api.get(`/api/campaigns/${id}/render`);
            setBriefingData(data);
            setEditedDraft(data.original_draft);
        } catch (error) {
            console.error("Failed to fetch rendered briefing data:", error);
            onClose();
        } finally {
            setIsLoading(false);
        }
    }, [api, onClose]);

    useEffect(() => {
        fetchData(briefingId);
    }, [briefingId, fetchData]);
    
    const handleSaveCommentary = async (resourceId: string, newCommentary: string) => {
        if (!briefingData) return;
        try {
            await api.put(`/api/campaigns/${briefingData.id}/matches/${resourceId}/commentary`, { commentary: newCommentary });
            // Optimistically update the local state
            setBriefingData(prev => {
                if (!prev) return null;
                return {
                    ...prev,
                    top_matches_rendered: prev.top_matches_rendered.map(match => 
                        match.resource_id === resourceId ? { ...match, agent_commentary: newCommentary } : match
                    )
                };
            });
        } catch (error) {
            console.error("Failed to save commentary:", error);
            // Optionally revert optimistic update here
        }
    };
    
    // Other handlers remain the same
    const handleRegenerate = async () => { if (!briefingData) return; setIsProcessing(true); try { await api.post(`/api/campaigns/${briefingData.id}/regenerate`, {}); await fetchData(briefingData.id); } catch (error) { console.error("Failed to regenerate briefing:", error); } finally { setIsProcessing(false); } };
    const handleDismiss = () => onClose();
    const handleSend = () => { alert("Send functionality to be implemented."); onClose(); };

    if (isLoading || !briefingData) {
        return <motion.div className="fixed inset-0 bg-gray-900/80 backdrop-blur-sm flex items-center justify-center z-50"><div className="text-white">Loading Nudge...</div></motion.div>;
    }
    
    const defaultConfig = { icon: 'Default', color: 'text-gray-400', title: 'Nudge' };
    const config = displayConfig[briefingData.campaign_type] || defaultConfig;
    const ICONS: Record<string, ReactNode> = { Home: <Home size={20} />, Default: <Info size={20}/> };
    const icon = ICONS[config.icon] || ICONS.Default;

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-[#111116]/80 backdrop-blur-md flex items-center justify-center z-50 p-4 md:p-8">
            <motion.div
                initial={{ scale: 0.95, y: 50, opacity: 0 }}
                animate={{ scale: 1, y: 0, opacity: 1 }}
                exit={{ scale: 0.95, y: -50, opacity: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="relative w-full max-w-4xl h-[95vh] max-h-[800px] bg-[#1C1C23] border border-gray-700 rounded-xl overflow-hidden flex flex-col shadow-2xl"
            >
                <header className="flex-shrink-0 p-4 bg-gray-900/50 border-b border-gray-700 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className={config.color}>{icon}</span>
                        <h3 className="font-bold text-lg text-white">{briefingData.headline}</h3>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={24}/></button>
                </header>

                <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-x-6 overflow-y-auto">
                    <div className="p-6 space-y-4">
                        <h4 className="font-semibold text-sm text-gray-400 flex items-center gap-2">Curated Matches ({briefingData.top_matches_rendered.length})</h4>
                        {briefingData.key_intel.curation_rationale && (
                            <div className="p-3 bg-indigo-900/30 border border-indigo-700/50 rounded-lg text-sm text-indigo-200 flex items-start gap-3">
                                <Info size={16} className="flex-shrink-0 mt-0.5" />
                                <div>
                                    <h5 className="font-bold">AI Curation Rationale</h5>
                                    <p>{briefingData.key_intel.curation_rationale}</p>
                                </div>
                            </div>
                        )}
                        <div className="space-y-3 max-h-[calc(80vh-200px)] overflow-y-auto pr-2">
                          {briefingData.top_matches_rendered.map(match => <RenderedMatchCard key={match.resource_id} match={match} onSave={handleSaveCommentary} />)}
                        </div>
                    </div>
                    <div className="p-6 space-y-5 flex flex-col border-l border-gray-700/50">
                        <div>
                            <h4 className="font-semibold text-sm text-gray-400 flex items-center gap-2 mb-3"><Users size={16}/> Audience</h4>
                            <div className="p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
                               <p className="font-semibold text-white text-base">{briefingData.matched_audience[0]?.client_name}</p>
                            </div>
                        </div>
                        <div className="flex-grow flex flex-col mt-4">
                            <h4 className="font-semibold text-sm text-gray-400 flex items-center gap-2 mb-2"><Edit size={16}/> Draft Message</h4>
                            <textarea value={editedDraft} onChange={(e) => setEditedDraft(e.target.value)} className="w-full flex-grow bg-gray-900 border border-gray-700 rounded-md focus:ring-2 focus:ring-indigo-500 text-gray-200 text-base p-4 resize-none leading-relaxed"/>
                        </div>
                    </div>
                </div>

                <footer className="flex-shrink-0 p-4 bg-gray-900/50 border-t border-gray-700 grid grid-cols-3 gap-3">
                    <button onClick={handleDismiss} className="p-3 bg-gray-700/50 border border-gray-600 text-white rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-gray-700"><X size={18} /> Dismiss</button>
                    <button onClick={handleRegenerate} disabled={isProcessing} className="p-3 bg-indigo-600/80 border border-indigo-500 text-white rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-indigo-600 disabled:opacity-50"><RefreshCw size={18} className={isProcessing ? 'animate-spin' : ''} /> Regenerate</button>
                    <button onClick={handleSend} className="p-3 text-white rounded-lg font-bold flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.4)] hover:scale-[1.03]" style={{ backgroundColor: '#10B981' }}><Send size={18} /> Send to Client</button>
                </footer>
            </motion.div>
        </motion.div>
    );
};