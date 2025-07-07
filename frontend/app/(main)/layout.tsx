// frontend/app/(main)/layout.tsx
// DEFINITIVE FIX: Adds a new "Community" link to the main navigation,
// while keeping the existing "All Conversations" link pointing to the dashboard.

'use client';

import { Suspense } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import { useAppContext } from '@/context/AppContext';
import { useSidebar } from '@/context/SidebarContext';
import { Avatar } from '@/components/ui/Avatar';
import { MessageCircleHeart, Users, Zap, Search, User as UserIcon } from "lucide-react"; // Imported Users icon

function MainLayoutContent({ children }: { children: React.ReactNode }) {
    const { conversations } = useAppContext();
    const router = useRouter();
    const pathname = usePathname();
    const { isSidebarOpen, setIsSidebarOpen } = useSidebar(); 
    
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
                {/* --- MODIFIED NAVIGATION SECTION --- */}
                <nav className="px-4 space-y-1.5 flex-shrink-0">
                    {/* NEW: Link to the Community page */}
                    <Link href="/community" className={clsx(
                        "flex items-center gap-3 p-2.5 rounded-lg transition-colors",
                        pathname === '/community' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5'
                    )}>
                        <Users className="w-5 h-5" /> Community
                    </Link>

                    {/* EXISTING: Link to the conversations view */}
                    <Link href="/dashboard" className={clsx(
                        "flex items-center gap-3 p-2.5 rounded-lg transition-colors",
                        pathname.startsWith('/conversations') || pathname === '/dashboard' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5'
                    )}>
                        <MessageCircleHeart className="w-5 h-5" /> All Conversations
                    </Link>

                    {/* EXISTING: Link to the Nudges page */}
                    <Link href="/nudges" className={clsx(
                        "flex items-center gap-3 p-2.5 rounded-lg transition-colors",
                        pathname === '/nudges' ? 'bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold' : 'text-brand-text-muted hover:bg-white/5'
                    )}>
                        <Zap className="w-5 h-5" /> AI Nudges
                    </Link>
                </nav>
                {/* ... (The rest of the sidebar remains unchanged) ... */}
                <div className="px-4 my-4 relative flex-shrink-0">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-text-muted/50" />
                    <input type="text" placeholder="Search conversations..." className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent" />
                </div>
                <div className="flex-grow overflow-y-auto px-4">
                    <ul className="space-y-1">
                        {conversations.map(conv => (
                            <li
                                key={conv.id}
                                className={clsx("p-3 rounded-lg cursor-pointer transition-colors border border-transparent", selectedClientId === conv.client_id ? "bg-white/10 border-white/20" : "hover:bg-white/5")}
                                onClick={() => handleConversationSelect(conv.client_id)}
                            >
                               <div className="flex items-start justify-between gap-3"><div className="flex items-start gap-3 overflow-hidden"><Avatar name={conv.client_name} className="w-10 h-10 text-sm flex-shrink-0" /><div className="overflow-hidden"><span className="font-semibold text-brand-text-main">{conv.client_name}</span><p className="text-brand-text-muted text-sm truncate">{conv.last_message}</p></div></div><div className="flex flex-col items-end flex-shrink-0"><span className="text-xs text-brand-text-muted/70">{new Date(conv.last_message_time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>{conv.unread_count > 0 && (<span className="mt-1 bg-brand-accent text-xs text-brand-dark font-bold rounded-full w-5 h-5 flex items-center justify-center"> {conv.unread_count} </span>)}</div></div>
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