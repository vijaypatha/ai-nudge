// ---
// File Path: frontend/app/nudges/page.tsx
// This version is updated to correctly pass the async save handler to the modal.
// No other logic is changed.
// ---

'use client'; 

// --- Imports ---
import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useAppContext } from '../../context/AppContext';
import type { Client } from '../../context/AppContext';
import { ManageAudienceModal } from './ManageAudienceModal';
import clsx from 'clsx';
import {
  MessageCircleHeart,
  Zap,
  User as UserIcon,
  Sparkles,
  Menu,
  BrainCircuit,
  Bot,
  Send,
  X,
  RefreshCw,
  PlusCircle,
  Lightbulb,
  ChevronDown,
  Users,
} from 'lucide-react';

// --- Type Definitions ---
interface MatchedClient {
  client_id: string;
  client_name: string;
  match_score: number;
  match_reason: string;
}

interface CampaignBriefing {
  id: string;
  headline: string;
  original_draft: string;
  matched_audience: MatchedClient[];
  status: 'new' | 'insight' | 'approved' | 'dismissed';
  key_intel: { [key: string]: string | number };
  edited_draft: string | null;
}

// --- Reusable Components ---
const Avatar = ({ name, className }: { name: string; className?: string }) => {
  const initials = name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase();
  return (
    <div
      className={clsx(
        'flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none',
        className
      )}
    >
      {initials}
    </div>
  );
};

// --- Nudge Card Components ---
const AiSuggestionCard = ({
  briefing,
  onUpdate,
  onManageAudience,
}: {
  briefing: CampaignBriefing;
  onUpdate: (updatedBriefing: CampaignBriefing) => void;
  onManageAudience: () => void;
}) => {
  const [isComposerVisible, setIsComposerVisible] = useState(false);
  const [draft, setDraft] = useState(briefing.original_draft);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAudienceExpanded, setIsAudienceExpanded] = useState(false);

  const topClient = briefing.matched_audience[0];
  const otherClients = briefing.matched_audience.slice(1);

  const handleUpdate = async (status: 'approved' | 'dismissed') => {
    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8001/campaigns/${briefing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited_draft: draft, status: status }),
      });
      if (!res.ok) throw new Error(`Failed to update campaign: ${res.statusText}`);
      const updatedData = await res.json();
      onUpdate(updatedData);
    } catch (error) {
      console.error('Error updating campaign:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={clsx(
        'bg-white/5 border border-white/10 rounded-xl overflow-hidden transition-opacity duration-500',
        briefing.status !== 'new' ? 'opacity-40' : ''
      )}
    >
      <header className="p-4 bg-black/10">
        <h3 className="font-bold text-lg text-brand-text-main flex items-center gap-3">
          <Sparkles size={18} className="text-green-400" /> {briefing.headline}
        </h3>
      </header>
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4 text-center">
          {Object.entries(briefing.key_intel).map(([key, value]) => (
            <div key={key} className="bg-black/20 p-3 rounded-md">
              <p className="text-sm text-brand-text-muted">{key}</p>
              <p className="font-bold text-lg text-brand-text-main">{value.toLocaleString()}</p>
            </div>
          ))}
          {briefing.key_intel['Potential Commission'] && (
            <p className="text-center text-xs text-brand-text-muted mb-4 -mt-2 col-span-2 md:col-span-3">
              *Assuming 1.5-3% commission range.
            </p>
          )}
        </div>
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-semibold text-brand-text-main">Suggested Audience</h4>
          <button onClick={onManageAudience} className="flex items-center gap-1.5 text-sm text-brand-accent hover:text-white">
            <PlusCircle size={14} />Manage Audience ({briefing.matched_audience.length})
          </button>
        </div>
        <div className="space-y-2">
          {briefing.matched_audience.length > 0 ? (
            <>
              {topClient && (
                <div className="flex items-center gap-3 bg-black/20 p-2.5 rounded-md">
                  <Avatar name={topClient.client_name} className="w-9 h-9 text-sm" />
                  <div className="flex-grow">
                    <p className="font-semibold text-base">{topClient.client_name}</p>
                    <p className="text-xs text-green-400 italic">✓ {topClient.match_reason}</p>
                  </div>
                </div>
              )}
              {otherClients.length > 0 &&
                (isAudienceExpanded ? (
                  otherClients.map((client) => (
                    <div key={client.client_id} className="flex items-center gap-3 bg-black/20 p-2.5 rounded-md">
                      <Avatar name={client.client_name} className="w-9 h-9 text-sm" />
                      <div className="flex-grow">
                        <p className="font-semibold text-base">{client.client_name}</p>
                        <p className="text-xs text-green-400 italic">✓ {client.match_reason}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <button
                    onClick={() => setIsAudienceExpanded(true)}
                    className="w-full text-left p-2 text-sm text-brand-text-muted hover:bg-black/40 rounded-md"
                  >
                    + {otherClients.length} other high-fit client(s)
                  </button>
                ))}
            </>
          ) : (
             <div className="text-center p-4 bg-black/20 rounded-md text-sm text-brand-text-muted">No audience selected.</div>
          )}
        </div>
      </div>
      <div className="p-4 border-t border-white/10 bg-black/10">
        {isComposerVisible ? (
          <div className="space-y-4">
            <h4 className="font-semibold text-brand-text-main">Edit Message Draft</h4>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="w-full h-32 bg-black/20 border border-white/20 rounded-lg p-3 text-sm"
              disabled={isSubmitting}
            />
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleUpdate('approved')}
                disabled={isSubmitting || briefing.status !== 'new'}
                className="flex-1 flex items-center justify-center gap-2 p-2.5 bg-primary-action text-brand-dark font-semibold rounded-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? <RefreshCw size={18} className="animate-spin" /> : <Send size={18} />}Send
              </button>
              <button
                onClick={() => handleUpdate('dismissed')}
                disabled={isSubmitting || briefing.status !== 'new'}
                className="p-2.5 bg-white/10 rounded-md hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Dismiss"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <p className="text-sm text-brand-text-muted">We've drafted a message for this nudge.</p>
            <button
              onClick={() => setIsComposerVisible(true)}
              className="flex items-center gap-2 text-sm font-semibold p-2 -mr-2 rounded-md hover:bg-white/10"
            >
              View & Send <ChevronDown size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const AiInsightCard = ({ briefing, onBuildAudience }: { briefing: CampaignBriefing, onBuildAudience: () => void; }) => {
  return (
    <div className="bg-black/20 border border-white/10 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4">
      <div className="flex-shrink-0">
        <Lightbulb size={20} className="text-amber-400" />
      </div>
      <div className="flex-grow text-center sm:text-left">
        <h3 className="font-semibold text-base text-brand-text-main">{briefing.headline}</h3>
        <p className="text-sm text-brand-text-muted">
          We didn't find a strong match for this, but you might know someone.
        </p>
      </div>
      <div className="flex-shrink-0 flex items-center gap-2">
        <button className="p-2.5 bg-white/10 rounded-md hover:bg-white/20 text-sm font-semibold">Dismiss</button>
        <button onClick={onBuildAudience} className="p-2.5 bg-primary-action text-brand-dark rounded-md text-sm font-semibold">
          Build Audience
        </button>
      </div>
    </div>
  );
};

const InsightGroupCard = ({ insights, onBuildAudience }: { insights: CampaignBriefing[], onBuildAudience: (briefing: CampaignBriefing) => void; }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  return (
    <div className="bg-white/5 border-2 border-dashed border-white/10 rounded-xl overflow-hidden">
      <header
        className="p-4 flex justify-between items-center cursor-pointer hover:bg-white/5"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 bg-black/20 rounded-lg">
            <BrainCircuit size={18} className="text-brand-text-muted" />
          </div>
          <div>
            <h3 className="font-bold text-lg text-brand-text-main">Market Insights</h3>
            <p className="text-sm text-brand-text-muted">
              {insights.length} unmatched opportunities. Add contacts and intel to get matches.
            </p>
          </div>
        </div>
        <ChevronDown size={20} className={clsx('transition-transform', isExpanded && 'rotate-180')} />
      </header>
      {isExpanded && (
        <div className="p-4 border-t border-white/10 space-y-4">
          {insights.map((briefing) => (
            <AiInsightCard key={briefing.id} briefing={briefing} onBuildAudience={() => onBuildAudience(briefing)} />
          ))}
        </div>
      )}
    </div>
  );
};

const InstantNudgeCreator = () => {
  const { clients } = useAppContext();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAudience, setSelectedAudience] = useState<Client[]>([]);

  const handleSaveAudience = async (newAudience: Client[]) => {
    setSelectedAudience(newAudience);
    // This is an async function to match the prop type, but doesn't need to do anything async here.
    return Promise.resolve();
  };
  
  const selectedAudienceIds = new Set(selectedAudience.map(c => c.id));

  return (
    <>
      <ManageAudienceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveAudience}
        allClients={clients}
        initialSelectedClientIds={selectedAudienceIds}
      />
      <div className="space-y-8">
        <section>
          <div className="flex items-center gap-3 mb-4">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">
              1
            </span>
            <h2 className="text-2xl font-bold">Target Your Audience</h2>
          </div>
          <div className="p-6 bg-white/5 rounded-xl border border-white/10">
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full p-4 bg-black/20 border-2 border-dashed border-white/20 rounded-xl flex flex-col items-center justify-center text-brand-text-muted hover:border-brand-accent hover:text-white transition-colors"
            >
              <Users size={24} className="mb-2" />
              <span className="font-semibold text-lg">Select Audience</span>
              <span className="text-sm">{selectedAudience.length} client(s) selected</span>
            </button>
          </div>
        </section>
        <section>
          <div className="flex items-center gap-3 mb-4">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">
              2
            </span>
            <h2 className="text-2xl font-bold">Draft and Send Nudge</h2>
          </div>
          <div className="p-6 bg-white/5 rounded-xl border border-white/10 space-y-4">
            <div>
              <label className="text-sm font-semibold text-brand-text-muted" htmlFor="topic">
                Topic / Goal (for AI draft)
              </label>
              <input
                id="topic"
                type="text"
                placeholder="e.g., End of quarter market update"
                className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-brand-text-muted" htmlFor="message">
                Message
              </label>
              <textarea
                id="message"
                rows={5}
                placeholder="Click 'Draft with AI' or write your own message..."
                className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"
              ></textarea>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <button className="flex items-center gap-2 p-3 bg-white/10 rounded-md font-semibold hover:bg-white/20">
                <Bot size={18} /> Draft with AI
              </button>
              <button className="flex items-center gap-2 p-3 bg-primary-action text-brand-dark rounded-md font-semibold hover:brightness-110">
                <Send size={18} /> Send to {selectedAudience.length} recipients
              </button>
            </div>
          </div>
        </section>
      </div>
    </>
  );
};

export default function NudgesPage() {
  const { clients } = useAppContext();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'ai_suggestions' | 'instant_nudge'>('ai_suggestions');
  const [briefings, setBriefings] = useState<CampaignBriefing[]>([]);
  const [loading, setLoading] = useState(true);

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<CampaignBriefing | null>(null);

  const fetchBriefings = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8001/nudges/');
      if (!res.ok) throw new Error(`Failed to fetch nudges: ${res.statusText}`);
      const data: CampaignBriefing[] = await res.json();
      setBriefings(data);
    } catch (err) {
      console.error('Error fetching nudges:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBriefings(); }, []);

  const handleCampaignUpdate = (updatedBriefing: CampaignBriefing) => {
    setBriefings((prevBriefings) =>
      prevBriefings.map((b) => (b.id === updatedBriefing.id ? updatedBriefing : b))
    );
  };

  const handleOpenAudienceModal = (briefing: CampaignBriefing) => {
    setEditingCampaign(briefing);
    setIsAudienceModalOpen(true);
  };
  
  const handleSaveAudience = async (newAudience: Client[]) => {
      if (!editingCampaign) return;

      const newMatchedAudience: MatchedClient[] = newAudience.map(client => ({
          client_id: client.id,
          client_name: client.full_name,
          match_score: 100,
          match_reason: 'Manually Added'
      }));

      // No try-catch here because the modal's handleSave will catch it.
      // Throwing the error ensures the modal knows the operation failed.
      const res = await fetch(`http://localhost:8001/campaigns/${editingCampaign.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ matched_audience: newMatchedAudience }),
      });

      if (!res.ok) {
          throw new Error('Failed to update audience on the server.');
      }
      
      const updatedCampaign: CampaignBriefing = await res.json();
      handleCampaignUpdate(updatedCampaign);
  };

  const highConfidenceNudges = briefings.filter((b) => b.status === 'new');
  const lowConfidenceInsights = briefings.filter((b) => b.status === 'insight');
  const initialSelectedClientIds = new Set(editingCampaign?.matched_audience.map(c => c.client_id) || []);

  return (
    <>
      <ManageAudienceModal
          isOpen={isAudienceModalOpen}
          onClose={() => setIsAudienceModalOpen(false)}
          onSave={handleSaveAudience}
          allClients={clients}
          initialSelectedClientIds={initialSelectedClientIds}
      />
      <div className="min-h-screen flex bg-brand-dark text-brand-text-main font-sans">
        {isSidebarOpen && (
          <div onClick={() => setIsSidebarOpen(false)} className="fixed inset-0 bg-black/50 z-10 md:hidden"></div>
        )}
        <aside
          className={clsx(
            'bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-20',
            'absolute md:relative inset-y-0 left-0 w-80',
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          )}
        >
          <div className="p-4 flex-shrink-0">
            <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority />
          </div>
          <nav className="px-4 space-y-1.5 flex-grow">
            <Link
              href="/dashboard"
              className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors"
            >
              <MessageCircleHeart className="w-5 h-5" /> All Conversations
            </Link>
            <Link
              href="/nudges"
              className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold"
            >
              <Zap className="w-5 h-5" /> AI Nudges
            </Link>
          </nav>
          <div className="p-4 flex-shrink-0 border-t border-white/5">
            <Link
              href="/profile"
              className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors"
            >
              <UserIcon className="w-5 h-5" /> Profile
            </Link>
          </div>
        </aside>
        <main className="flex-1 p-6 sm:p-10 overflow-y-auto">
          <header className="flex items-start sm:items-center justify-between gap-4 mb-8 flex-col sm:flex-row">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden"
              >
                <Menu className="w-6 h-6" />
              </button>
              <h1 className="text-3xl font-bold">AI Nudges</h1>
            </div>
            <div className="bg-black/20 p-1 rounded-lg flex items-center gap-1 self-stretch sm:self-auto">
              <button
                onClick={() => setActiveTab('ai_suggestions')}
                className={clsx(
                  'px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none',
                  { 'bg-white/10': activeTab === 'ai_suggestions' }
                )}
              >
                AI Suggestions
              </button>
              <button
                onClick={() => setActiveTab('instant_nudge')}
                className={clsx(
                  'px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none',
                  { 'bg-white/10': activeTab === 'instant_nudge' }
                )}
              >
                Instant Nudge
              </button>
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
                    <p className="mt-1 text-sm text-brand-text-muted">
                      The AI is watching the market. New opportunities will appear here.
                    </p>
                  </div>
                )}
                {highConfidenceNudges.map((briefing) => (
                  <AiSuggestionCard 
                    key={briefing.id} 
                    briefing={briefing} 
                    onUpdate={handleCampaignUpdate} 
                    onManageAudience={() => handleOpenAudienceModal(briefing)}
                  />
                ))}
                {lowConfidenceInsights.length > 0 && 
                  <InsightGroupCard 
                    insights={lowConfidenceInsights} 
                    onBuildAudience={handleOpenAudienceModal} 
                  />}
              </div>
            )}
            {activeTab === 'instant_nudge' && <InstantNudgeCreator />}
          </div>
        </main>
      </div>
    </>
  );
}