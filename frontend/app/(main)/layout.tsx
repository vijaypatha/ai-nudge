// frontend/app/(main)/layout.tsx
// DEFINITIVE FIX: This version integrates the reusable <MagicSearchBar /> into the
// main sidebar, allowing users to search for conversations using natural language.

'use client';

import { useState, Suspense, useEffect, useCallback } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import { useAppContext } from '@/context/AppContext';
import { useSidebar } from '@/context/SidebarContext';
import { Avatar } from '@/components/ui/Avatar';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar'; // Import the MagicSearchBar
import { MessageCircleHeart, Users, Zap, User as UserIcon, Menu } from "lucide-react";

function MainLayoutContent({ children }: { children: React.ReactNode }) {
    const { conversations: initialConversations, api } = useAppContext();
    const router = useRouter();
    const pathname = usePathname();
    const { isSidebarOpen, setIsSidebarOpen } = useSidebar(); 
    
    // State for the search functionality
    const [displayedConversations, setDisplayedConversations] = useState(initialConversations);
    const [isSearching, setIsSearching] = useState(false);

    // When the initial conversations from context change, update our local display list
    useEffect(() => {
        setDisplayedConversations(initialConversations);
    }, [initialConversations]);

    const handleConversationSearch = useCallback(async (query: string) => {
        setIsSearching(true);
        if (!query.trim()) {
            setDisplayedConversations(initialConversations); // Reset if query is empty
            setIsSearching(false);
            return;
        }
        try {
            const searchResults = await api.post('/api/clients/search', { natural_language_query: query });
            // The search returns clients, so we need to find the matching conversations
            const searchedClientIds = new Set(searchResults.map((client: any) => client.id));
            const filteredConversations = initialConversations.filter(conv => searchedClientIds.has(conv.client_id));
            setDisplayedConversations(filteredConversations);
        } catch (error) {
            console.error("Failed to search conversations:", error);
            setDisplayedConversations([]); // Clear results on error
        } finally {
            setIsSearching(false);
        }
    }, [api, initialConversations]);
    
    const selectedClientId = pathname.includes('/conversations/') ? pathname.split('/').pop() : null;

    const handleConversationSelect = (clientId: string) => {
        router.push(`/conversations/${clientId}`);
        setIsSidebarOpen(false);
    };

    return (
        <div className="h-screen w-screen bg-brand-dark text-brand-text-main font-sans flex overflow-hidden">
            {isSidebarOpen && (
                <div onClick={() => setIsSidebarOpen(false)} className="fixed inset-0 bg-black/50 z-30 md:hidden"></div>
            )}

            <aside className={clsx(
                "bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-40",
                "absolute md:relative inset-y-0 left-0 w-80",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
            )}>
                <div className="p-4 flex-shrink-0">
                    <button onClick={() => router.push('/dashboard')}>
                        <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority />
                    </button>
                </div>
                <nav className="px-4 space-y-1.5 flex-shrink-0">
                    <Link href="/community" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname === '/community' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                        <Users className="w-5 h-5" /> Community
                    </Link>
                    <Link href="/dashboard" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname.startsWith('/conversations') || pathname === '/dashboard' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                        <MessageCircleHeart className="w-5 h-5" /> All Conversations
                    </Link>
                    <Link href="/nudges" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname === '/nudges' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                        <Zap className="w-5 h-5" /> AI Nudges
                    </Link>
                </nav>
                
                {/* MODIFIED: Replaced static input with MagicSearchBar */}
                <div className="px-4 my-4 flex-shrink-0">
                    <MagicSearchBar 
                        onSearch={handleConversationSearch}
                        isLoading={isSearching}
                        placeholder="Search  topics..."
                    />
                </div>

                <div className="flex-grow overflow-y-auto px-4">
                    <ul className="space-y-1">
                        {displayedConversations.map(conv => (
                            <li
                                key={conv.id}
                                className={clsx("p-3 rounded-lg cursor-pointer transition-colors border border-transparent", selectedClientId === conv.client_id ? "bg-white/10 border-white/20" : "hover:bg-white/5")}
                                onClick={() => handleConversationSelect(conv.client_id)}
                            >
                               <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-start gap-3 overflow-hidden">
                                        <Avatar name={conv.client_name} className="w-10 h-10 text-sm flex-shrink-0" />
                                        <div className="overflow-hidden">
                                            <span className="font-semibold text-brand-text-main">{conv.client_name}</span>
                                            <p className="text-brand-text-muted text-sm truncate">{conv.last_message}</p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end flex-shrink-0">
                                        <span className="text-xs text-brand-text-muted/70">
                                            {new Date(conv.last_message_time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                                        </span>
                                        {conv.unread_count > 0 && (
                                            <span className="mt-1 bg-brand-accent text-xs text-brand-dark font-bold rounded-full w-5 h-5 flex items-center justify-center">
                                                {conv.unread_count}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="p-4 flex-shrink-0 border-t border-white/5">
                    <Link href="/profile" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
                        <UserIcon className="w-5 h-5" /> Profile
                    </Link>
                </div>
            </aside>
            {children}
        </div>
    );
}

export default function MainLayout({ children }: { children: React.ReactNode }) {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <MainLayoutContent>{children}</MainLayoutContent>
        </Suspense>
    );
}
