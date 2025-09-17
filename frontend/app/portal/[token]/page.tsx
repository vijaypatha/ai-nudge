// frontend/app/portal/[token]/page.tsx
// --- The public-facing, interactive client portal ---

'use client';

import { useState, useEffect, FC } from 'react';
import { format } from 'date-fns';
import Image from 'next/image';
import { Heart, ThumbsUp, ThumbsDown, Send, Loader2, AlertTriangle, X, CheckSquare, Edit } from 'lucide-react';

// --- Types (mirroring backend structures) ---
interface PortalPreferences {
    [key: string]: any;
}

interface MediaItem {
    MediaURL: string;
}

interface PortalMatch {
    id: string;
    attributes: {
        UnparsedAddress?: string;
        ListPrice?: number;
        BedroomsTotal?: number;
        BathroomsTotalInteger?: number;
        LivingArea?: number;
        PublicRemarks?: string;
        Media?: MediaItem[];
        agent_commentary?: string;
    };
    status: string;
    mls_status?: string;
}

interface GroupedMatch {
    curation_date: string;
    matches: { resource: PortalMatch; [key: string]: any }[];
}

interface PortalData {
    client_name: string;
    preferences: PortalPreferences;
    matches: GroupedMatch[];
    agent_name?: string;
    curation_rationale?: string;
    survey_completed: boolean;
    survey_template: any | null; // Placeholder for survey structure
}



// --- API Client ---
const api = {
    get: async (url: string) => {
        const res = await fetch(url);
        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(error.detail || `API Error: ${res.statusText}`);
        }
        return res.json();
    },
    post: async (url: string, data: any) => {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(error.detail || `API Error: ${res.statusText}`);
        }
        return res.json();
    }
};

// --- Sub-Components for the Portal UI ---

const Lightbox: FC<{ images: string[]; startIndex: number; onClose: () => void }> = ({ images, startIndex, onClose }) => {
    const [currentIndex, setCurrentIndex] = useState(startIndex);

    const handleNext = () => setCurrentIndex((prev) => (prev + 1) % images.length);
    const handlePrev = () => setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowRight') handleNext();
            if (e.key === 'ArrowLeft') handlePrev();
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    return (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50" onClick={onClose}>
            <button className="absolute top-4 right-4 text-white hover:text-cyan-400 z-50" onClick={onClose}><X size={32} /></button>
            <div className="relative w-[90vw] h-[80vh]" onClick={(e) => e.stopPropagation()}>
                <Image src={images[currentIndex]} alt="Enlarged property view" layout="fill" objectFit="contain" />
            </div>
            {images.length > 1 && (
                <>
                    <button onClick={(e) => { e.stopPropagation(); handlePrev(); }} className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/40 text-white p-2 rounded-full hover:bg-black/70">‹</button>
                    <button onClick={(e) => { e.stopPropagation(); handleNext(); }} className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/40 text-white p-2 rounded-full hover:bg-black/70">›</button>
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/50 text-white text-sm px-3 py-1 rounded-md">
                        {currentIndex + 1} / {images.length}
                    </div>
                </>
            )}
        </div>
    );
};

const PreferenceChip: FC<{ label: string; value: any }> = ({ label, value }) => {
    if (!value && value !== 0) return null;
    const displayValue = Array.isArray(value) ? value.join(', ') : value;
    return (
        <div className="bg-gray-700/50 border border-white/10 rounded-full px-4 py-2 text-center">
            <p className="text-xs text-gray-400">{label}</p>
            <p className="text-white font-semibold text-sm">{displayValue}</p>
        </div>
    );
};

const PropertyCard: FC<{ resource: PortalMatch; token: string; onImageClick: (images: string[], index: number) => void }> = ({ resource, token, onImageClick }) => {
    const [feedback, setFeedback] = useState<'love' | 'like' | 'dislike' | null>(null);
    const [comment, setComment] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const attr = resource.attributes;
    const allPhotos = attr.Media?.map(m => m.MediaURL).filter(Boolean) || [];
    const imageUrl = allPhotos.length > 0 ? allPhotos[currentImageIndex] : `https://placehold.co/600x400/1A1D24/FFFFFF?text=${attr.UnparsedAddress?.split(',')[0]}`;
    
    const handleNextImage = (e: React.MouseEvent) => { e.stopPropagation(); setCurrentImageIndex((prev) => (prev + 1) % allPhotos.length); };
    const handlePrevImage = (e: React.MouseEvent) => { e.stopPropagation(); setCurrentImageIndex((prev) => (prev - 1 + allPhotos.length) % allPhotos.length); };

    // --- NEW: Status Banner Logic ---
    const StatusBanner = () => {
        const statusText = resource.mls_status || resource.status;
        if (!statusText || statusText.toLowerCase() === 'active') return null;

        const statusColor = statusText.toLowerCase().includes('sold') || statusText.toLowerCase().includes('closed') ? 'bg-red-600'
            : statusText.toLowerCase().includes('pending') || statusText.toLowerCase().includes('under contract') ? 'bg-orange-500'
            : 'bg-gray-600';

        return <div className={`absolute top-2 left-2 ${statusColor} text-white text-xs font-bold px-2 py-1 rounded-md z-10`}>{statusText.toUpperCase()}</div>;
    };

    const handleFeedback = async (action: 'love' | 'like' | 'dislike') => {
        setFeedback(action);
        try {
            await api.post(`/api/portal/feedback/${token}`, { resource_id: resource.id, action });
        } catch (e) { console.error(e); }
    };

    const handleCommentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!comment.trim()) return;
        setIsSubmitting(true);
        try {
            await api.post(`/api/portal/feedback/${token}`, { resource_id: resource.id, action: 'comment', comment_text: comment });
            setComment('');
        } catch (e) { console.error(e); } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="bg-gray-800/50 border border-white/10 rounded-2xl overflow-hidden shadow-lg flex flex-col">
            <div className="relative w-full h-48 group cursor-pointer" onClick={() => onImageClick(allPhotos, currentImageIndex)}>
                <StatusBanner />
                <Image src={imageUrl} alt={`Image of ${attr.UnparsedAddress}`} layout="fill" objectFit="cover" />
                {allPhotos.length > 1 && (
                    <>
                        <button onClick={handlePrevImage} className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/40 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-10">‹</button>
                        <button onClick={handleNextImage} className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/40 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-10">›</button>
                        <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded-md">{currentImageIndex + 1} / {allPhotos.length}</div>
                    </>
                )}
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

                {attr.agent_commentary && <div className="mt-3 text-sm text-cyan-200 bg-cyan-500/10 p-3 rounded-lg border border-cyan-500/20"><span className="font-bold">📝 Agent's Note:</span> {attr.agent_commentary}</div>}
                
                {attr.PublicRemarks && (
                    <div className="mt-3 text-sm text-gray-300">
                        <p className={`whitespace-pre-wrap ${!isExpanded ? 'line-clamp-3' : ''}`}>
                            {attr.PublicRemarks}
                        </p>
                        <button onClick={() => setIsExpanded(!isExpanded)} className="text-cyan-400 hover:text-cyan-300 text-xs mt-1">
                            {isExpanded ? 'Show less' : 'Show more...'}
                        </button>
                    </div>
                )}

                <div className="mt-auto pt-4 border-t border-white/10">
                    <div className="flex justify-around items-center">
                        <button onClick={() => handleFeedback('love')} className={`p-2 rounded-full transition-colors ${feedback === 'love' ? 'bg-pink-500/20 text-pink-400' : 'hover:bg-white/10 text-gray-400'}`}><Heart size={20} /></button>
                        <button onClick={() => handleFeedback('like')} className={`p-2 rounded-full transition-colors ${feedback === 'like' ? 'bg-green-500/20 text-green-400' : 'hover:bg-white/10 text-gray-400'}`}><ThumbsUp size={20} /></button>
                        <button onClick={() => handleFeedback('dislike')} className={`p-2 rounded-full transition-colors ${feedback === 'dislike' ? 'bg-red-500/20 text-red-400' : 'hover:bg-white/10 text-gray-400'}`}><ThumbsDown size={20} /></button>
                    </div>
                    
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

// --- NEW: Kickoff view for clients who haven't completed their survey ---
const SurveyKickoffView: FC<{ portalData: PortalData }> = ({ portalData }) => (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 lg:p-8 text-center">
        <header className="mb-12">
            <h1 className="text-4xl font-bold text-white">Welcome, {portalData.client_name}!</h1>
            <p className="mt-2 text-lg text-gray-400">Let's get started by confirming a few details.</p>
        </header>
        <div className="bg-gray-800/50 border border-dashed border-white/10 rounded-2xl p-8">
            <Edit className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-white mb-2">Help Us Find Your Perfect Match</h2>
            <p className="text-gray-400 mb-6">
                Your feedback helps us tailor your experience. Please take a moment to complete your intake survey.
            </p>
            <button className="bg-cyan-500 text-white font-bold py-2 px-6 rounded-lg hover:bg-cyan-600 transition-colors">
                Start Survey
            </button>
        </div>
        <footer className="text-center mt-16 text-gray-500 text-xs">
            {portalData.agent_name && <p>This portal was personally prepared for you by {portalData.agent_name}.</p>}
        </footer>
    </div>
);

// --- NEW: The main Hub view for ongoing interaction ---
const HubView: FC<{ portalData: PortalData; token: string; onOpenLightbox: (images: string[], index: number) => void }> = ({ portalData, token, onOpenLightbox }) => (
     <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        <header className="text-center mb-12">
            <h1 className="text-4xl font-bold text-white">Welcome, {portalData.client_name}</h1>
            <p className="mt-2 text-lg text-gray-400">Here is your personalized home search portal.</p>
        </header>
        
        {portalData.curation_rationale && (
             <section className="mb-12 max-w-3xl mx-auto">
                <div className="bg-gray-800/50 border border-white/10 rounded-xl p-6">
                    <h2 className="text-xl font-semibold mb-3 text-cyan-400">A Note From Your Agent</h2>
                    <p className="text-gray-300 whitespace-pre-wrap">{portalData.curation_rationale}</p>
                </div>
            </section>
        )}

        <section className="mb-16">
            <h2 className="text-2xl font-semibold text-center mb-6">Confirming Your Vision</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
                <PreferenceChip label="Max Budget" value={portalData.preferences.budget_max?.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 })} />
                <PreferenceChip label="Min Bedrooms" value={portalData.preferences.min_bedrooms} />
                <PreferenceChip label="Min Bathrooms" value={portalData.preferences.min_bathrooms} />
                <PreferenceChip label="Location(s)" value={portalData.preferences.locations} />
            </div>
        </section>
        
        <section>
            <h2 className="text-3xl font-bold text-center mb-12">Your Curated Matches</h2>
            {portalData.matches && portalData.matches.length > 0 ? (
                <div className="space-y-12">
                    {portalData.matches.map((group: GroupedMatch) => (
                        <div key={group.curation_date}>
                            <h3 className="text-lg font-semibold text-gray-400 mb-6 pl-2 border-l-4 border-cyan-500">
                                Matches Found on {format(new Date(group.curation_date), 'MMMM d, yyyy')}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {group.matches.map((match: any) => <PropertyCard key={match.resource.id} resource={match.resource} token={token} onImageClick={(imgs, idx) => onOpenLightbox(imgs, idx)} />)}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-12 bg-gray-800/50 border border-dashed border-white/10 rounded-2xl">
                    <CheckSquare className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
                    <p className="text-gray-300">Your agent is currently curating your first set of matches.</p>
                    <p className="text-gray-500 text-sm mt-1">Check back soon!</p>
                </div>
            )}
        </section>
        
        <footer className="text-center mt-16 text-gray-500 text-xs">
            {portalData.agent_name && <p>This portal was personally prepared for you by {portalData.agent_name}.</p>}
        </footer>
    </div>
);

// --- Main Page Component ---
export default function PortalPage({ params }: { params: { token: string }}) {
    const { token } = params;
    const [portalData, setPortalData] = useState<PortalData | null>(null);
    const [pageState, setPageState] = useState<'loading' | 'error' | 'loaded'>('loading');
    const [errorMsg, setErrorMsg] = useState('This link may be invalid or expired.');

    const [lightboxImages, setLightboxImages] = useState<string[]>([]);
    const [lightboxStartIndex, setLightboxStartIndex] = useState(0);
    const isLightboxOpen = lightboxImages.length > 0;

    const handleOpenLightbox = (images: string[], startIndex: number) => {
        setLightboxImages(images);
        setLightboxStartIndex(startIndex);
    };
    const handleCloseLightbox = () => setLightboxImages([]);

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
                setErrorMsg(err.message || 'This link may be invalid or expired.');
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
            {isLightboxOpen && <Lightbox images={lightboxImages} startIndex={lightboxStartIndex} onClose={handleCloseLightbox} />}
            <main>
                {/* --- MODIFICATION: Conditionally render Hub or Survey view --- */}
                {portalData.survey_completed ? (
                    <HubView portalData={portalData} token={token} onOpenLightbox={handleOpenLightbox} />
                ) : (
                    <SurveyKickoffView portalData={portalData} />
                )}
            </main>
        </div>
    );
}