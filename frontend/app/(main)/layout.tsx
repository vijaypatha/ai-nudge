// frontend/app/(main)/layout.tsx
// --- MODIFIED ---
// Purpose: Adds detailed diagnostic logging to the conversation search function
// to identify why search results may not be appearing on the frontend.

'use client';

import { useState, Suspense, useEffect, useCallback, useMemo } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import { useAppContext } from '@/context/AppContext';
import { useSidebar } from '@/context/SidebarContext';
import { Avatar } from '@/components/ui/Avatar';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar';
import { ConversationListItem } from '@/components/conversation/ConversationListItem';
import { MessageCircleHeart, Users, Zap, User as UserIcon, Menu, RefreshCw, Clock, TrendingUp } from "lucide-react";

// Pipeline Status Indicator Component
const PipelineStatusIndicator = () => {
    const [status, setStatus] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchStatus = useCallback(async () => {
        try {
            const response = await fetch('http://localhost:8001/api/pipeline-status');
            if (response.ok) {
                const data = await response.json();
                setStatus(data);
            } else {
                setStatus({ status: 'error', hours_ago: null });
            }
        } catch (error) {
            console.error('Failed to fetch pipeline status:', error);
            setStatus({ status: 'error', hours_ago: null });
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStatus();
        // Refresh status every 5 minutes
        const interval = setInterval(fetchStatus, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    if (isLoading) {
        return (
            <div className="mt-2 p-2 text-xs text-brand-text-muted bg-white/5 rounded-lg">
                <div className="flex items-center gap-2">
                    <Clock className="w-3 h-3" />
                    <span>Loading status...</span>
                </div>
            </div>
        );
    }

    const getStatusColor = () => {
        if (status?.status === 'active' && status?.hours_ago !== null) {
            if (status.hours_ago <= 2) return 'text-green-400';
            if (status.hours_ago <= 4) return 'text-yellow-400';
            return 'text-red-400';
        }
        return 'text-brand-text-muted';
    };

    const getStatusText = () => {
        if (status?.status === 'active' && status?.hours_ago !== null) {
            return `Last updated: ${status.hours_ago} hours ago`;
        }
        return 'Status unknown';
    };

    return (
        <div className="mt-2 p-2 text-xs bg-white/5 rounded-lg">
            <div className="flex items-center gap-2">
                <Clock className={`w-3 h-3 ${getStatusColor()}`} />
                <span className={getStatusColor()}>{getStatusText()}</span>
            </div>
        </div>
    );
};

export default function MainLayout({ children }: { children: React.ReactNode }) {
    const { conversations: initialConversations, api, forceRefreshAllData, user } = useAppContext();
    const router = useRouter();
    const pathname = usePathname();
    const { isSidebarOpen, setIsSidebarOpen } = useSidebar();

    const [searchedConversations, setSearchedConversations] = useState<any[] | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const sortedInitialConversations = useMemo(() => {
        return [...initialConversations].sort((a, b) =>
            new Date(b.last_message_time).getTime() - new Date(a.last_message_time).getTime()
        );
    }, [initialConversations]);

    const displayedConversations = searchedConversations ?? sortedInitialConversations;

    const handleForceRefresh = async () => {
        setIsRefreshing(true);
        try {
            await forceRefreshAllData();
            console.log("Data refreshed successfully");
        } catch (error) {
            console.error("Failed to refresh data:", error);
        } finally {
            setIsRefreshing(false);
        }
    };

    const handleConversationSearch = useCallback(async (query: string) => {
        setIsSearching(true);
        if (!query.trim()) {
            setSearchedConversations(null);
            setIsSearching(false);
            return;
        }
        try {
            // Call the new, dedicated search endpoint for conversations.
            const searchResults = await api.post('/api/conversations/search', { natural_language_query: query });
            // The result is already a list of conversation summaries, so no
            // client-side filtering is needed. This is faster and more reliable.
            setSearchedConversations(searchResults);
        } catch (error) {
            console.error("Failed to search conversations:", error);
            setSearchedConversations([]);
        } finally {
            setIsSearching(false);
        }
    }, [api]);

    const selectedClientId = pathname.includes('/conversations/') ? pathname.split('/').pop() : null;

    const handleConversationSelect = async (clientId: string) => {
        // Validate that the client ID exists in the current conversations list
        const clientExists = displayedConversations.some(conv => conv.client_id === clientId);
        if (!clientExists) {
            console.warn(`Client ID ${clientId} not found in current conversations, refreshing data...`);
            await handleForceRefresh();
            return;
        }

        router.push(`/conversations/${clientId}`);
        setIsSidebarOpen(false);
        
        // Mark messages as read when conversation is selected
        try {
            await api.post(`/api/conversations/${clientId}/mark-read`, {});
        } catch (error) {
            console.error("Failed to mark messages as read:", error);
        }
    };

    return (
        <Suspense fallback={<div>Loading...</div>}>
            <div className="h-screen w-screen bg-brand-dark text-brand-text-main font-sans flex overflow-hidden">
                {isSidebarOpen && (
                    <div onClick={() => setIsSidebarOpen(false)} className="fixed inset-0 bg-black/50 z-30 md:hidden"></div>
                )}

                <aside className={clsx(
                    "bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-50 [backface-visibility:hidden]",
                    "absolute md:relative inset-y-0 left-0 w-80",
                    isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
                )}>
                    <div className="p-4 flex-shrink-0">
                        <button onClick={() => router.push('/dashboard')}>
                            <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} sizes="260px" priority  />
                        </button>
                    </div>
                    <nav className="px-4 space-y-1.5 flex-shrink-0">
                        <Link href="/community" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname === '/community' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                            <Users className="w-5 h-5" /> Community
                        </Link>
                        <Link href="/dashboard" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname.startsWith('/conversations') || pathname === '/dashboard' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                            <MessageCircleHeart className="w-5 h-5" /> All Conversations
                        </Link>
                        {(user?.user_type === 'realtor' || user?.super_user) && (
                            <Link href="/market-activity" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname === '/market-activity' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                                <TrendingUp className="w-5 h-5" /> Live Market Activity
                            </Link>
                        )}
                        <Link href="/nudges" className={clsx("flex items-center gap-3 p-2.5 rounded-lg transition-colors", pathname === '/nudges' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5')}>
                            <Zap className="w-5 h-5" /> My AI Nudges
                        </Link>
                    </nav>

                    <div className="px-4 my-4 flex-shrink-0">
                        <MagicSearchBar
                            onSearch={handleConversationSearch}
                            isLoading={isSearching}
                            placeholder="Search topics..."
                        />
                        <button
                            onClick={handleForceRefresh}
                            disabled={isRefreshing}
                            className="mt-2 w-full flex items-center justify-center gap-2 p-2 text-xs text-brand-text-muted hover:text-brand-text-main hover:bg-white/5 rounded-lg transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
                            {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
                        </button>
                        
                        {/* Pipeline Status Indicator */}
                        <PipelineStatusIndicator />
                    </div>

                    <div className="flex-grow overflow-y-auto">
                        {/* Header */}
                        <div className="px-4 py-3 border-b border-white/10">
                            <h2 className="text-lg font-semibold text-brand-text-main">Recent Conversations</h2>
                            <p className="text-xs text-brand-text-muted mt-1">
                                {displayedConversations.length} conversation{displayedConversations.length !== 1 ? 's' : ''}
                            </p>
                        </div>
                        
                        {/* Conversations List */}
                        <div className="space-y-1">
                            {displayedConversations.length === 0 ? (
                                <div className="p-8 text-center text-brand-text-muted">
                                    <MessageCircleHeart className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p className="text-sm">No conversations yet</p>
                                    <p className="text-xs mt-1">Start messaging your clients to see them here</p>
                                </div>
                            ) : (
                                displayedConversations.map(conv => (
                                    <ConversationListItem
                                        key={conv.id}
                                        conversation={conv}
                                        isSelected={selectedClientId === conv.client_id}
                                        onClick={() => handleConversationSelect(conv.client_id)}
                                    />
                                ))
                            )}
                        </div>
                    </div>
                    <div className="p-4 flex-shrink-0 border-t border-white/5">
                        <Link href="/profile" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
                            <UserIcon className="w-5 h-5" /> Profile
                        </Link>
                    </div>
                </aside>
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Mobile header with hamburger menu */}
                    <header className="flex items-center justify-between p-4 border-b border-white/10 bg-brand-dark/50 backdrop-blur-sm sticky top-0 z-40 md:hidden">
                        <button 
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
                            className="p-2 rounded-full text-brand-text-muted hover:bg-white/10"
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                        <div className="flex items-center gap-2">
                            <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={120} height={30} priority />
                        </div>
                        <div className="w-10"></div> {/* Spacer for centering */}
                    </header>
                    {children}
                </div>
            </div>
        </Suspense>
    );
}