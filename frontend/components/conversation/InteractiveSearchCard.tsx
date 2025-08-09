// frontend/components/conversation/InteractiveSearchCard.tsx
'use client';

import { InfoCard } from '@/components/ui/InfoCard';
import { Button } from '@/components/ui/Button';
import { Loader2, Search, ArrowRight } from 'lucide-react';
import Image from 'next/image';

// Define the structure of a single search result
// This should mirror the InteractiveSearchResponse from the backend
interface InteractiveSearchResult {
    event_id: string;
    headline: string;
    resource: {
        address?: string;
        price?: number;
        beds?: number;
        baths?: number;
        attributes: any;
    };
    score: number;
    reasons: string[];
}

interface InteractiveSearchCardProps {
    onSearch: () => void;
    isSearching: boolean;
    results: InteractiveSearchResult[];
}

export const InteractiveSearchCard = ({ onSearch, isSearching, results }: InteractiveSearchCardProps) => {
    return (
        <InfoCard
            title="Interactive Search"
            icon={<Search className="w-4 h-4" />}
            headerAction={
                <Button variant="secondary" size="sm" onClick={onSearch} disabled={isSearching}>
                    {isSearching ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                        <Search className="w-4 h-4 mr-2" />
                    )}
                    Find Matches
                </Button>
            }
        >
            <div className="space-y-4">
                {isSearching && (
                    <div className="text-center text-brand-text-muted py-4">Searching for properties...</div>
                )}

                {!isSearching && results.length === 0 && (
                    <p className="text-sm text-brand-text-muted">
                        Click "Find Matches" to search for properties based on the client's latest intel.
                    </p>
                )}

                {!isSearching && results.length > 0 && (
                    <ul className="space-y-3">
                        {results.map((item) => (
                            <li key={item.event_id} className="text-sm p-3 bg-brand-dark rounded-md border border-white/10">
                                <div className="flex items-center gap-3">
                                    <div className="relative w-16 h-12 bg-brand-dark-blue rounded-md overflow-hidden flex-shrink-0">
                                        <Image 
                                            src={item.resource.attributes?.Media?.[0]?.MediaURL || `https://placehold.co/300x200/0B112B/C4C4C4?text=Property`}
                                            alt={`Image of ${item.headline}`}
                                            layout="fill"
                                            objectFit="cover"
                                        />
                                    </div>
                                    <div className="flex-grow min-w-0">
                                        <p className="font-semibold text-brand-text-main truncate">{item.headline}</p>
                                        <p className="text-xs text-brand-text-muted">
                                            {item.resource.beds} bd | {item.resource.baths} ba | ${item.resource.price?.toLocaleString()}
                                        </p>
                                    </div>
                                    <button className="p-1.5 rounded-full text-brand-text-muted hover:bg-white/10 flex-shrink-0">
                                        <ArrowRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </InfoCard>
    );
};