// frontend/components/ui/MagicSearchBar.tsx
// Purpose: A reusable, debounced search bar for natural language queries.

'use client';

import { useState, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface MagicSearchBarProps {
    onSearch: (query: string) => void;
    isLoading: boolean;
    placeholder?: string;
    className?: string;
}

export const MagicSearchBar = ({ onSearch, isLoading, placeholder = "AI Nudge Magic Search...", className }: MagicSearchBarProps) => {
    const [query, setQuery] = useState('');

    // Debounce effect to trigger search after user stops typing
    useEffect(() => {
        const handler = setTimeout(() => {
            onSearch(query);
        }, 500); // 500ms delay

        return () => {
            clearTimeout(handler);
        };
    }, [query, onSearch]);

    return (
        <div className={`relative ${className}`}>
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                {isLoading ? (
                    <Loader2 size={18} className="text-brand-text-muted animate-spin" />
                ) : (
                    <Search size={18} className="text-brand-text-muted" />
                )}
            </div>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={placeholder}
                className="w-full bg-black/20 border border-white/20 rounded-lg p-3 pl-10 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
            />
        </div>
    );
};
