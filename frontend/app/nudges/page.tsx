// File Path: frontend/app/nudges/page.tsx
// Purpose: This page serves as the user's central hub for all outbound campaigns. This version makes the "AI Suggestions" card fully interactive, allowing users to edit, approve, and dismiss campaigns.

'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useAppContext } from '../../context/AppContext';
import type { Client } from '../../context/AppContext';
import clsx from 'clsx';
import { 
  MessageCircleHeart, Zap, User as UserIcon, Sparkles, Menu, Users, BrainCircuit, Bot, Send, Calendar, Edit2, Check, X, RefreshCw
} from "lucide-react";


// --- Type Definitions ---
interface MatchedClient {
  client_id: string;
  client_name: string;
  match_score: number;
  match_reason: string;
}

interface CampaignBriefing {
  id: string;
  user_id: string;
  campaign_type: string;
  headline: string;
  key_intel: Record<string, any>;
  listing_url: string | null;
  original_draft: string;
  edited_draft: string | null;
  matched_audience: MatchedClient[];
  status: string;
  created_at: string;
}

// --- Reusable Components ---
const Avatar = ({ name, className }: { name: string, className?: string }) => {
  const initials = name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
  return (<div className={clsx("flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none", className)}> {initials} </div>);
};


// --- Nudges Page Components ---

const AiSuggestionCard = ({ briefing, onUpdate }: { briefing: CampaignBriefing; onUpdate: (updatedBriefing: CampaignBriefing) => void; }) => {
  // This component displays a single AI-generated campaign and handles its state changes.
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(briefing.edited_draft || briefing.original_draft);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleUpdate = async (status: 'approved' | 'dismissed') => {
    // This function calls the new backend endpoint to update the campaign status.
    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8001/campaigns/${briefing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          edited_draft: draft,
          status: status,
        }),
      });
      if (!res.ok) throw new Error(`Failed to update campaign to ${status}`);
      const updatedData = await res.json();
      onUpdate(updatedData); // Update the parent component's state
    } catch (error) {
      console.error(error);
      alert(`Error: Could not ${status} the campaign.`);
    } finally {
      setIsSubmitting(false);
      setIsEditing(false);
    }
  };

  const handleSaveEdit = () => {
    // This function saves the draft without changing the campaign status.
    // It's a "soft save" before approving.
    briefing.edited_draft = draft; // Optimistic update
    setIsEditing(false);
    // Note: A more robust solution might auto-save to the backend here as well.
  };

  return (
    <div className={clsx("bg-white/5 border border-white/10 rounded-xl overflow-hidden transition-opacity duration-500", briefing.status !== 'new' ? 'opacity-40' : '')}>
      <header className="p-4 bg-black/10">
        <h3 className="font-bold text-lg text-brand-text-main">{briefing.headline}</h3>
        <p className="text-sm text-brand-text-muted">Opportunity found on {new Date(briefing.created_at).toLocaleDateString()}</p>
      </header>
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left side: Draft and Actions */}
        <div className="space-y-4">
          <h4 className="font-semibold text-brand-text-muted">AI-Generated Draft</h4>
          {isEditing ? (
            <textarea 
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="w-full h-40 bg-black/20 border border-white/20 rounded-lg p-3 text-sm"
              disabled={isSubmitting}
            />
          ) : (
            <p className="text-sm bg-black/20 p-3 rounded-md whitespace-pre-wrap">{draft}</p>
          )}
          {/* Action buttons change based on whether the user is editing the draft. */}
          {isEditing ? (
             <div className="flex items-center gap-2">
                <button onClick={handleSaveEdit} disabled={isSubmitting} className="flex-1 p-2.5 bg-primary-action text-brand-dark font-semibold rounded-md hover:brightness-110">
                    Save Draft
                </button>
                <button onClick={() => {setIsEditing(false); setDraft(briefing.edited_draft || briefing.original_draft)}} disabled={isSubmitting} className="p-2.5 bg-white/10 rounded-md hover:bg-white/20">
                    Cancel
                </button>
             </div>
          ) : (
            <div className="flex items-center gap-2">
                <button onClick={() => handleUpdate('approved')} disabled={isSubmitting || briefing.status !== 'new'} className="flex-1 flex items-center justify-center gap-2 p-2.5 bg-primary-action text-brand-dark font-semibold rounded-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed">
                {isSubmitting && briefing.status === 'new' ? <RefreshCw size={18} className="animate-spin" /> : <Check size={18} />}
                {briefing.status === 'approved' ? 'Approved & Sent' : 'Approve & Send'}
                </button>
                <button onClick={() => setIsEditing(true)} disabled={isSubmitting || briefing.status !== 'new'} className="p-2.5 bg-white/10 rounded-md hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed">
                    <Edit2 size={18} />
                </button>
                <button onClick={() => handleUpdate('dismissed')} disabled={isSubmitting || briefing.status !== 'new'} className="p-2.5 bg-white/10 rounded-md hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed">
                    {briefing.status === 'dismissed' ? 'Dismissed' : <X size={18} />}
                </button>
            </div>
          )}
        </div>
        {/* Right side: Audience */}
        <div className="space-y-3">
           <h4 className="font-semibold text-brand-text-muted">Suggested Audience ({briefing.matched_audience.length})</h4>
           <div className="max-h-48 overflow-y-auto space-y-2 pr-2">
            {briefing.matched_audience.map(client => (
              <div key={client.client_id} className="flex items-center gap-3 bg-black/20 p-2 rounded-md">
                <Avatar name={client.client_name} className="w-8 h-8 text-xs" />
                <div>
                  <p className="font-semibold text-sm">{client.client_name}</p>
                  <p className="text-xs text-brand-text-muted italic opacity-80">{client.match_reason}</p>
                </div>
              </div>
            ))}
           </div>
        </div>
      </div>
    </div>
  );
};


const InstantNudgeCreator = () => {
  // This component's functionality will be wired up next. No changes in this step.
  const { clients } = useAppContext();
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);
  const [selectedClients, setSelectedClients] = useState<Set<string>>(new Set());
  
  useEffect(() => {
    setFilteredClients(clients);
  }, [clients]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedClients(new Set(filteredClients.map(c => c.id)));
    } else {
      setSelectedClients(new Set());
    }
  };

  const handleSelectClient = (clientId: string) => {
    const newSelection = new Set(selectedClients);
    if (newSelection.has(clientId)) {
      newSelection.delete(clientId);
    } else {
      newSelection.add(clientId);
    }
    setSelectedClients(newSelection);
  };
  
  return (
    <div className="space-y-8">
      <section>
        <div className="flex items-center gap-3 mb-4">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">1</span>
          <h2 className="text-2xl font-bold">Target Your Audience</h2>
        </div>
        <div className="p-6 bg-white/5 rounded-xl border border-white/10">
            <label className="text-sm font-semibold text-brand-text-muted" htmlFor="audience-builder">Natural Language Audience Builder ✨</label>
            <input id="audience-builder" type="text" placeholder="e.g., “investors I haven't talked to in six months”" className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"/>
            <div className="my-4 text-center text-sm text-brand-text-muted">or use traditional filters</div>
            <div className="border border-white/10 rounded-lg max-h-64 overflow-y-auto">
                <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-dark/50 backdrop-blur-sm">
                    <label className="flex items-center gap-3 text-sm">
                        <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClients.size > 0 && selectedClients.size === filteredClients.length} onChange={handleSelectAll} />
                        Select All Filtered ({selectedClients.size}/{filteredClients.length})
                    </label>
                </div>
                {filteredClients.map(client => (
                    <div key={client.id} className="border-b border-white/10 last:border-b-0">
                         <label className="flex items-center gap-3 p-3 hover:bg-white/5 cursor-pointer">
                            <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClients.has(client.id)} onChange={() => handleSelectClient(client.id)} />
                            <Avatar name={client.full_name} className="w-8 h-8 text-xs"/>
                            {client.full_name}
                        </label>
                    </div>
                ))}
            </div>
        </div>
      </section>
      <section>
        <div className="flex items-center gap-3 mb-4">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">2</span>
          <h2 className="text-2xl font-bold">Draft and Send Nudge</h2>
        </div>
         <div className="p-6 bg-white/5 rounded-xl border border-white/10 space-y-4">
            <div>
                <label className="text-sm font-semibold text-brand-text-muted" htmlFor="topic">Topic / Goal (for AI draft)</label>
                <input id="topic" type="text" placeholder="e.g., End of quarter market update" className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"/>
            </div>
            <div>
                <label className="text-sm font-semibold text-brand-text-muted" htmlFor="message">Message</label>
                <textarea id="message" rows={5} placeholder="Click 'Draft with AI' or write your own message..." className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"></textarea>
            </div>
            <div className="flex flex-wrap items-center gap-4">
                <button className="flex items-center gap-2 p-3 bg-white/10 rounded-md font-semibold hover:bg-white/20">
                    <Bot size={18} /> Draft with AI
                </button>
                <button className="flex items-center gap-2 p-3 bg-primary-action text-brand-dark rounded-md font-semibold hover:brightness-110">
                    <Send size={18} /> Send to {selectedClients.size} recipients
                </button>
            </div>
        </div>
      </section>
    </div>
  );
};


// --- Main Nudges Page Component ---
export default function NudgesPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'ai_suggestions' | 'instant_nudge'>('ai_suggestions');
  const [briefings, setBriefings] = useState<CampaignBriefing[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchBriefings = async () => {
    // This function fetches AI-generated campaigns from the backend.
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8001/nudges/');
      if (!res.ok) throw new Error("Failed to fetch nudges.");
      const data: CampaignBriefing[] = await res.json();
      setBriefings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBriefings();
  }, []);

  const handleCampaignUpdate = (updatedBriefing: CampaignBriefing) => {
    // This function updates the local state after a campaign is approved or dismissed,
    // which allows the UI to react instantly (e.g., by dimming the card).
    setBriefings(prevBriefings => 
      prevBriefings.map(b => b.id === updatedBriefing.id ? updatedBriefing : b)
    );
  };

  return (
    <div className="min-h-screen flex bg-brand-dark text-brand-text-main font-sans">
      {/* Sidebar Backdrop for Mobile */}
      {isSidebarOpen && (<div onClick={() => setIsSidebarOpen(false)} className="fixed inset-0 bg-black/50 z-10 md:hidden"></div>)}
      {/* Left Sidebar: Navigation */}
      <aside className={clsx("bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-20", "absolute md:relative inset-y-0 left-0 w-80", isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0")}>
        <div className="p-4 flex-shrink-0">
          <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority />
        </div>
        <nav className="px-4 space-y-1.5 flex-grow">
          <Link href="/dashboard" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
            <MessageCircleHeart className="w-5 h-5" /> All Conversations
          </Link>
          <Link href="/nudges" className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold">
            <Zap className="w-5 h-5" /> AI Nudges
          </Link>
        </nav>
        <div className="p-4 flex-shrink-0 border-t border-white/5">
           <Link href="/profile" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
            <UserIcon className="w-5 h-5" /> Profile
          </Link>
        </div>
      </aside>
      {/* Main Content Area */}
      <main className="flex-1 p-6 sm:p-10 overflow-y-auto">
        <header className="flex items-start sm:items-center justify-between gap-4 mb-8 flex-col sm:flex-row">
            <div className="flex items-center gap-4">
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden"><Menu className="w-6 h-6" /></button>
                <h1 className="text-3xl font-bold">AI Nudges</h1>
            </div>
            <div className="bg-black/20 p-1 rounded-lg flex items-center gap-1 self-stretch sm:self-auto">
                <button onClick={() => setActiveTab('ai_suggestions')} className={clsx("px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none", {'bg-white/10': activeTab === 'ai_suggestions'})}>AI Suggestions</button>
                 <button onClick={() => setActiveTab('instant_nudge')} className={clsx("px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none", {'bg-white/10': activeTab === 'instant_nudge'})}>Instant Nudge</button>
            </div>
        </header>
        <div>
            {activeTab === 'ai_suggestions' && (
                <div className="space-y-6">
                    {loading && <p>Loading suggestions...</p>}
                    {!loading && briefings.length === 0 && (
                        <div className="text-center py-16 border-2 border-dashed border-white/10 rounded-xl">
                            <BrainCircuit className="mx-auto h-12 w-12 text-brand-text-muted" />
                            <h3 className="mt-2 text-lg font-medium">No AI Suggestions Yet</h3>
                            <p className="mt-1 text-sm text-brand-text-muted">The AI is watching the market. New opportunities will appear here.</p>
                        </div>
                    )}
                    {briefings.filter(b => b.status === 'new').length === 0 && !loading && briefings.length > 0 && (
                         <div className="text-center py-16 border-2 border-dashed border-white/10 rounded-xl">
                            <Check className="mx-auto h-12 w-12 text-green-400" />
                            <h3 className="mt-2 text-lg font-medium">All Caught Up!</h3>
                            <p className="mt-1 text-sm text-brand-text-muted">You've reviewed all available AI suggestions.</p>
                        </div>
                    )}
                    {briefings.map(briefing => (
                        <AiSuggestionCard key={briefing.id} briefing={briefing} onUpdate={handleCampaignUpdate} />
                    ))}
                </div>
            )}
            {activeTab === 'instant_nudge' && (<InstantNudgeCreator />)}
        </div>
      </main>
    </div>
  );
}