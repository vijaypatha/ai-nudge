// frontend/app/portal/[token]/page.tsx
// --- The public-facing, interactive client portal ---

'use client';

import { useState, useEffect, FC } from 'react';
import Image from 'next/image';
import { Heart, ThumbsUp, ThumbsDown, MessageSquare, Send, Loader2, AlertTriangle } from 'lucide-react';

// --- Types (mirroring backend structures) ---
interface PortalPreferences {
    [key: string]: any;
}

interface PortalMatch {
    id: string; // This would be the resource_id
    attributes: {
        UnparsedAddress?: string;
        ListPrice?: number;
        BedroomsTotal?: number;
        BathroomsTotalInteger?: number;
        LivingArea?: number;
        PublicRemarks?: string;
        Media?: { MediaURL: string }[];
        agent_commentary?: string;
    };
    // We will add the "Agent's Note" here in a future step
}

interface PortalData {
    client_name: string;
    preferences: PortalPreferences;
    matches: PortalMatch[];
    comments: any[]; // Placeholder for now
}

// --- API Client (a simple fetcher for this public page) ---
const api = {
    get: async (url: string) => {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return res.json();
    },
    post: async (url: string, data: any) => {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return res.json();
    }
};

// --- Sub-Components for the Portal UI ---

const PreferenceChip: FC<{ label: string; value: any }> = ({ label, value }) => {
    if (!value) return null;
    const displayValue = Array.isArray(value) ? value.join(', ') : value;
    return (
        <div className="bg-gray-700/50 border border-white/10 rounded-full px-4 py-2 text-center">
            <p className="text-xs text-gray-400">{label}</p>
            <p className="text-white font-semibold text-sm">{displayValue}</p>
        </div>
    );
};

const PropertyCard: FC<{ match: PortalMatch; token: string }> = ({ match, token }) => {
    const [feedback, setFeedback] = useState<'love' | 'like' | 'dislike' | null>(null);
    const [comment, setComment] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    const attr = match.attributes;
    const imageUrl = attr.Media?.find(m => m.MediaURL)?.MediaURL || `https://placehold.co/600x400/1A1D24/FFFFFF?text=${attr.UnparsedAddress?.split(',')[0]}`;
    const agentCommentary = attr.agent_commentary; // Get the new commentary

    const handleFeedback = async (action: 'love' | 'like' | 'dislike') => {
        setFeedback(action);
        setIsSubmitting(true);
        try {
            await api.post(`/api/portal/feedback/${token}`, { resource_id: match.id, action });
        } catch (e) { console.error(e); } finally {
            setIsSubmitting(false);
        }
    };

    const handleCommentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!comment.trim()) return;
        setIsSubmitting(true);
        try {
            await api.post(`/api/portal/feedback/${token}`, { resource_id: match.id, action: 'comment', comment_text: comment });
            setComment(''); // Clear input on success
        } catch (e) { console.error(e); } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="bg-gray-800/50 border border-white/10 rounded-2xl overflow-hidden shadow-lg flex flex-col">
            <div className="relative w-full h-48">
                <Image src={imageUrl} alt={`Image of ${attr.UnparsedAddress}`} layout="fill" objectFit="cover" />
            </div>
            <div className="p-4 flex flex-col flex-grow">
                <p className="text-sm font-semibold text-white truncate">{attr.UnparsedAddress}</p>
                <div className="flex justify-between items-center mt-2">
                    <p className="text-lg font-bold text-cyan-400">${attr.ListPrice?.toLocaleString()}</p>
                    <div className="flex gap-3 text-xs text-gray-300">
                        <span>{attr.BedroomsTotal} bd</span>
                        <span>{attr.BathroomsTotalInteger} ba</span>
                        <span>{attr.LivingArea?.toLocaleString()} sqft</span>
                    </div>
                </div>

                {/* --- [THIS IS THE NEW UI] --- */}
                {agentCommentary && (
                    <div className="mt-3 text-sm text-cyan-200 bg-cyan-500/10 p-3 rounded-lg border border-cyan-500/20">
                        <span className="font-bold">📝 Agent's Note:</span> {agentCommentary}
                    </div>
                )}
                {/* --- [END NEW UI] --- */}

                <div className="mt-auto">
                    {/* Feedback Controls */}
                    <div className="mt-4 flex justify-around items-center border-t border-white/10 pt-3">
                        <button onClick={() => handleFeedback('love')} className={`p-2 rounded-full transition-colors ${feedback === 'love' ? 'bg-pink-500/20 text-pink-400' : 'hover:bg-white/10 text-gray-400'}`}><Heart size={20} /></button>
                        <button onClick={() => handleFeedback('like')} className={`p-2 rounded-full transition-colors ${feedback === 'like' ? 'bg-green-500/20 text-green-400' : 'hover:bg-white/10 text-gray-400'}`}><ThumbsUp size={20} /></button>
                        <button onClick={() => handleFeedback('dislike')} className={`p-2 rounded-full transition-colors ${feedback === 'dislike' ? 'bg-red-500/20 text-red-400' : 'hover:bg-white/10 text-gray-400'}`}><ThumbsDown size={20} /></button>
                    </div>
                    
                    {/* Comment Form */}
                    <form onSubmit={handleCommentSubmit} className="mt-3 flex gap-2">
                        <input 
                            type="text"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="Add a comment..."
                            className="flex-grow bg-gray-700/50 border border-white/10 rounded-full px-4 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
                        />
                        <button type="submit" disabled={isSubmitting} className="p-2 bg-cyan-500 text-white rounded-full hover:bg-cyan-600 disabled:opacity-50">
                            {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

// --- Main Page Component ---
export default function PortalPage({ params }: { params: { token: string }}) {
    const { token } = params;
    const [portalData, setPortalData] = useState<PortalData | null>(null);
    const [pageState, setPageState] = useState<'loading' | 'error' | 'loaded'>('loading');
    const [errorMsg, setErrorMsg] = useState('This link may be invalid or expired.');

    useEffect(() => {
        if (!token) {
            setPageState('error');
            return;
        }
        const fetchData = async () => {
            try {
                const data = await api.get(`/api/portal/view/${token}`);
                setPortalData(data);
                setPageState('loaded');
            } catch (err: any) {
                if (err.message.includes('403')) setErrorMsg('This portal link is expired or invalid. Please request a new one from your agent.');
                setPageState('error');
            }
        };
        fetchData();
    }, [token]);

    if (pageState === 'loading') {
        return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white"><Loader2 size={32} className="animate-spin text-cyan-400" /></div>;
    }

    if (pageState === 'error' || !portalData) {
        return (
            <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-white p-4 text-center">
                <AlertTriangle size={48} className="text-yellow-400 mb-4" />
                <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
                <p className="text-gray-400 max-w-md">{errorMsg}</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white font-sans">
            <main className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
                {/* Header */}
                <header className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-white">Welcome, {portalData.client_name}</h1>
                    <p className="mt-2 text-lg text-gray-400">Here is your personalized home search portal.</p>
                </header>

                {/* Part A: Confirming Your Vision */}
                <section className="mb-16">
                    <h2 className="text-2xl font-semibold text-center mb-6">Confirming Your Vision</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
                        <PreferenceChip label="Max Budget" value={portalData.preferences.budget_max?.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 })} />
                        <PreferenceChip label="Min Bedrooms" value={portalData.preferences.min_bedrooms} />
                        <PreferenceChip label="Min Bathrooms" value={portalData.preferences.min_bathrooms} />
                        <PreferenceChip label="Location(s)" value={portalData.preferences.locations} />
                    </div>
                </section>
                
                {/* Part B: Curated Matches */}
                <section>
                    <h2 className="text-2xl font-semibold text-center mb-8">Your Curated Matches</h2>
                    {portalData.matches.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {portalData.matches.map(match => (
                                <PropertyCard key={match.id} match={match} token={token} />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 bg-gray-800/50 border border-dashed border-white/10 rounded-2xl">
                            <p className="text-gray-400">Your agent is currently curating your first set of matches.</p>
                            <p className="text-gray-500 text-sm mt-1">Check back soon!</p>
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
}