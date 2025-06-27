// File Path: frontend/app/profile/page.tsx
// Purpose: Renders the Agent Profile page. This version includes the fix for the mobile sidebar overlay to ensure a consistent, professional look and feel.

'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { MessageCircleHeart, Zap, User as UserIcon, Sparkles, Menu } from "lucide-react";
import clsx from 'clsx';

// --- Type Definition ---
interface User {
  id: string;
  full_name: string;
  email: string;
  market_focus: string[];
  strategy: {
    nudge_format: string;
  };
}

// --- Reusable Components ---
const InfoCard = ({ title, children, className }: { title: string, children: React.ReactNode, className?: string }) => (
  <div className={clsx("bg-white/5 border border-white/10 rounded-xl", className)}>
    <div className="px-4 pt-4 pb-2">
      <h3 className="text-sm font-semibold text-brand-text-muted">{title}</h3>
    </div>
    <div className="p-4 pt-0"> {children} </div>
  </div>
);

const Avatar = ({ name, className }: { name: string, className?: string }) => {
  const initials = name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
  return (<div className={clsx("flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none", className)}> {initials} </div>);
};

const CurrentUserCard = ({ user }: { user: User | null }) => {
  if (!user) return null;
  return (
    <InfoCard title="Agent Profile">
      <div className="flex flex-col items-center text-center p-4">
        <Avatar name={user.full_name} className="w-24 h-24 text-4xl mb-4" />
        <h3 className="text-2xl font-bold text-brand-text-main">{user.full_name}</h3>
        <p className="text-base text-brand-text-muted mb-6">{user.email}</p>
        <div className="w-full max-w-sm space-y-4 text-left">
          <div>
            <p className="text-xs text-brand-text-muted mb-1">Market Focus:</p>
            <div className="flex flex-wrap gap-2">
              {user.market_focus.map(market => (
                <span key={market} className="bg-brand-accent/20 text-brand-accent text-sm font-semibold px-3 py-1 rounded-full">
                  {market}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-brand-text-muted mb-1">Strategy:</p>
            <p className="text-lg text-brand-text-main capitalize">{user.strategy.nudge_format}</p>
          </div>
        </div>
      </div>
    </InfoCard>
  );
};

// --- Main Profile Page Component ---
export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // State for mobile sidebar

  useEffect(() => {
    // This function fetches the current user's data from the backend.
    const fetchUser = async () => {
      try {
        setLoading(true);
        const usersRes = await fetch('http://localhost:8001/users');
        if (!usersRes.ok) {
          throw new Error(`Failed to fetch users: ${usersRes.statusText}`);
        }
        const usersData: User[] = await usersRes.json();
        if (usersData.length > 0) {
          setUser(usersData[0]); // Use the mock user
        } else {
          throw new Error('No user data found.');
        }
      } catch (err: any) {
        setError(err.message || "An unknown error occurred");
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  return (
    <div className="min-h-screen flex bg-brand-dark text-brand-text-main font-sans">
      {/* BUG FIX: This backdrop div darkens the main content when the mobile menu is open. */}
      {isSidebarOpen && (
        <div 
          onClick={() => setIsSidebarOpen(false)} 
          className="fixed inset-0 bg-black/50 z-10 md:hidden"
        ></div>
      )}

      {/* Left Sidebar: Navigation */}
      <aside className={clsx(
        "bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-20", // BUG FIX: Higher z-index and solid background
        "absolute md:relative inset-y-0 left-0 w-80",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        <div className="p-4 flex-shrink-0">
          <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority />
        </div>
        <nav className="px-4 space-y-1.5 flex-grow">
          <Link href="/dashboard" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
            <MessageCircleHeart className="w-5 h-5" /> All Conversations
          </Link>
          <Link href="/nudges" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
            <Zap className="w-5 h-5" /> AI Nudges
          </Link>
        </nav>
        <div className="p-4 flex-shrink-0 border-t border-white/5">
           <Link href="/profile" className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold">
            <UserIcon className="w-5 h-5" /> Profile
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 sm:p-10 overflow-y-auto">
        <header className="flex items-center gap-4 mb-8">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden">
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-3xl font-bold">Agent Profile</h1>
        </header>

        {loading && (
          <div className="flex justify-center items-center h-64">
            <Sparkles className="w-10 h-10 text-brand-accent animate-spin" />
          </div>
        )}
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-lg">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}
        {!loading && !error && (
          <div className="max-w-4xl mx-auto">
            <CurrentUserCard user={user} />
          </div>
        )}
      </main>
    </div>
  );
}