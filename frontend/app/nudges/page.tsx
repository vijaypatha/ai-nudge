// frontend/app/nudges/page.tsx
'use client';

import { useState, useEffect, useMemo } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import clsx from 'clsx';
import { useAppContext } from '../../context/AppContext';
import type { Client, Message, CampaignBriefing, MatchedClient } from '../../context/AppContext';
import {
  MessageCircleHeart, Zap, Sparkles, Send, CheckCircle, ArrowRight,
  Users, TrendingUp, Tag, ArrowDownCircle, ExternalLink, UserPlus, X
} from "lucide-react";

// --- REUSABLE SUB-COMPONENTS ---
const IntelChip = ({ icon, label, value }: { icon: React.ReactNode, label: string, value: string | number }) => (
  <div className="flex flex-col bg-white/5 p-3 rounded-lg text-center flex-grow">
    <div className="mx-auto text-brand-accent">{icon}</div>
    <span className="text-xs text-brand-text-muted mt-1">{label}</span>
    <span className="text-sm font-bold text-white">{value}</span>
  </div>
);

// --- MODAL COMPONENT ---
const EditAudienceModal = ({
  isOpen,
  onClose,
  onSave,
  initialAudience,
  allClients
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newAudience: MatchedClient[]) => void;
  initialAudience: MatchedClient[];
  allClients: Client[];
}) => {
  const [currentAudience, setCurrentAudience] = useState(initialAudience);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    setCurrentAudience(initialAudience);
  }, [initialAudience]);

  if (!isOpen) return null;

  const audienceIds = new Set(currentAudience.map(c => c.client_id));
  const otherClients = allClients
    .filter(c => !audienceIds.has(c.id))
    .filter(c => c.full_name.toLowerCase().includes(searchTerm.toLowerCase()));

  const addClient = (client: Client) => {
    const newMatchedClient: MatchedClient = {
      client_id: client.id,
      client_name: client.full_name,
      match_score: 0,
      match_reason: "Manually Added by Agent"
    };
    setCurrentAudience([...currentAudience, newMatchedClient]);
  };

  const removeClient = (clientId: string) => {
    setCurrentAudience(currentAudience.filter(c => c.client_id !== clientId));
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-brand-dark border border-white/10 rounded-2xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl">
        <header className="p-6 border-b border-white/10 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Edit Campaign Audience</h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-white/10"><X size={20}/></button>
        </header>
        <div className="grid grid-cols-2 gap-px bg-white/10 flex-grow overflow-hidden">
            <div className="bg-brand-dark p-6 flex flex-col">
                <h3 className="font-semibold text-white mb-4">Target Audience ({currentAudience.length})</h3>
                <ul className="space-y-2 overflow-y-auto pr-2">
                    {currentAudience.map(client => (
                        <li key={client.client_id} className="flex items-center justify-between bg-white/5 p-3 rounded-lg animate-fade-in">
                            <div>
                                <p className="text-sm font-medium">{client.client_name}</p>
                                <p className="text-xs text-brand-text-muted">{client.match_reason}</p>
                            </div>
                            <button onClick={() => removeClient(client.client_id)} className="p-1.5 text-red-400 hover:bg-red-400/10 rounded-full"><X size={16}/></button>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="bg-brand-dark p-6 flex flex-col">
                <h3 className="font-semibold text-white mb-4">Add Other Clients</h3>
                <input type="text" placeholder="Search all clients..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 mb-4 text-sm"/>
                <ul className="space-y-2 overflow-y-auto pr-2">
                    {otherClients.map(client => (
                        <li key={client.id} className="flex items-center justify-between bg-white/5 p-3 rounded-lg">
                            <span className="text-sm">{client.full_name}</span>
                            <button onClick={() => addClient(client)} className="p-1.5 text-green-400 hover:bg-green-400/10 rounded-full"><UserPlus size={16}/></button>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
        <footer className="p-6 border-t border-white/10 flex justify-end gap-4">
            <button onClick={onClose} className="px-5 py-2.5 text-sm font-semibold bg-white/10 hover:bg-white/20 rounded-md">Cancel</button>
            <button onClick={() => onSave(currentAudience)} className="px-5 py-2.5 text-sm font-semibold bg-primary-action text-brand-dark hover:brightness-110 rounded-md">Save Audience</button>
        </footer>
      </div>
    </div>
  );
};

// --- CARD COMPONENT ---
const IntelSuggestionCard = ({ briefing }: { briefing: CampaignBriefing }) => {
    const { clients, setClients } = useAppContext();
    const [isAdded, setIsAdded] = useState(false);

    const handleAddIntel = async () => {
        const client = clients.find(c => c.id === briefing.client_id);
        if (!client) return;
        const newNotes = [...(client.preferences.notes || []), briefing.original_draft];
        const updatedPreferences = { ...client.preferences, notes: newNotes };
        const res = await fetch(`http://localhost:8001/clients/${client.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preferences: updatedPreferences })
        });
        if (res.ok) {
            const updatedClient = await res.json();
            setClients(prev => prev.map(c => c.id === updatedClient.id ? updatedClient : c));
            setIsAdded(true);
        } else {
            alert("Failed to add intel.");
        }
    };

    if (isAdded) {
        return (
            <div className="bg-white/10 border border-green-400/30 rounded-xl p-6 flex items-center gap-4 shadow-lg">
                <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
                <div>
                    <h3 className="font-bold text-white">Intel Added!</h3>
                    <p className="text-sm text-brand-text-muted">The campaign for {clients.find(c => c.id === briefing.client_id)?.full_name} can now be updated.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gradient-to-br from-blue-500/10 to-white/0 border border-blue-400/30 rounded-xl p-6 shadow-2xl space-y-4">
            <h3 className="text-xl font-bold text-white">{briefing.headline}</h3>
            <div className="bg-white/5 p-4 rounded-lg">
                <p className="text-sm text-brand-text-muted mb-1">Suggested Note:</p>
                <p className="text-base text-white font-medium">"{briefing.original_draft}"</p>
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                <button className="px-5 py-2.5 text-sm font-semibold text-brand-text-main bg-white/10 hover:bg-white/20 rounded-md">Dismiss</button>
                <button onClick={handleAddIntel} className="px-5 py-2.5 text-sm font-semibold text-white bg-blue-500 hover:bg-blue-400 rounded-md">Add to Profile</button>
            </div>
        </div>
    );
};

const CampaignBriefingCard = ({ briefing, allClients, onUpdate }: { briefing: CampaignBriefing, allClients: Client[], onUpdate: (updatedBriefing: CampaignBriefing) => void }) => {
  const { setConversations } = useAppContext();
  const [editedMessage, setEditedMessage] = useState(briefing.original_draft);
  const [isLaunched, setIsLaunched] = useState(false);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleLaunchCampaign = async () => {
    setIsLaunching(true);
    for (const client of briefing.matched_audience) {
      await fetch('http://localhost:8001/campaigns/messages/send-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: client.client_id, content: editedMessage }),
      });
      const newMessage: Message = { id: `msg-${Date.now()}-${client.client_id}`, sender: 'agent', content: editedMessage, timestamp: new Date().toISOString() };
      setConversations(prev => prev.map(conv => 
        conv.client_id === client.client_id
          ? { ...conv, messages: [...conv.messages, newMessage], last_message: editedMessage, last_message_time: new Date().toISOString() }
          : conv
      ));
    }
    setIsLaunching(false);
    setIsLaunched(true);
  };

  const handleSaveAudience = (newAudience: MatchedClient[]) => {
    onUpdate({ ...briefing, matched_audience: newAudience });
    setIsModalOpen(false);
  };

  if (isLaunched) {
    return (
      <div className="bg-white/10 border border-green-400/30 rounded-xl p-6 flex flex-col items-center text-center shadow-lg transition-all duration-300">
        <CheckCircle className="w-12 h-12 text-green-400 mb-3" />
        <h3 className="text-lg font-bold text-white">Campaign Launched!</h3>
        <p className="text-sm text-brand-text-muted">Messages sent to {briefing.matched_audience.length} clients.</p>
      </div>
    );
  }

  return (
    <>
      <EditAudienceModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSave={handleSaveAudience} initialAudience={briefing.matched_audience} allClients={allClients} />
      <div className="bg-gradient-to-br from-white/5 to-white/0 border border-white/10 rounded-xl p-6 shadow-2xl space-y-6">
        <div className="flex justify-between items-start gap-4">
            <h3 className="text-xl font-bold text-white">{briefing.headline}</h3>
            {briefing.listing_url && ( <a href={briefing.listing_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm font-semibold text-brand-text-muted hover:text-brand-accent transition-colors flex-shrink-0 ml-4">View Listing <ExternalLink className="w-4 h-4" /></a> )}
        </div>
        <div>
            <h4 className="text-sm font-semibold text-brand-text-muted mb-3">Key Intel</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {briefing.key_intel.price_change && <IntelChip icon={<ArrowDownCircle size={20} />} label="Price Change" value={briefing.key_intel.price_change} />}
                {briefing.key_intel.new_price && <IntelChip icon={<Tag size={20} />} label="New Price" value={briefing.key_intel.new_price} />}
                {briefing.key_intel.market_comparison && <IntelChip icon={<TrendingUp size={20} />} label="Market Comp" value={briefing.key_intel.market_comparison} />}
            </div>
        </div>
        <div>
          <div className="flex justify-between items-center mb-2">
            <h4 className="text-sm font-semibold text-brand-text-muted">Target Audience</h4>
            <button onClick={() => setIsModalOpen(true)} className="text-xs font-semibold text-brand-accent hover:underline flex items-center gap-1.5 p-1 rounded-md hover:bg-brand-accent/10">
              <UserPlus size={14}/> Edit Audience
            </button>
          </div>
          <p className="text-2xl font-bold text-white">{briefing.matched_audience.length} Clients</p>
        </div>
        <div>
            <h4 className="text-sm font-semibold text-brand-text-muted mb-3">Master Message (SMS Optimized)</h4>
            <textarea value={editedMessage} onChange={(e) => setEditedMessage(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent transition-all" rows={5}/>
        </div>
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button className="px-5 py-2.5 text-sm font-semibold text-brand-text-main bg-white/10 hover:bg-white/20 rounded-md transition-colors">Dismiss</button>
            <button onClick={handleLaunchCampaign} disabled={isLaunching || briefing.matched_audience.length === 0} className="px-5 py-2.5 text-sm font-semibold text-brand-dark bg-primary-action hover:brightness-110 rounded-md flex items-center gap-2 transition-opacity disabled:opacity-50">
                {isLaunching ? 'Launching...' : `Launch Campaign (${briefing.matched_audience.length})`}
                <Send className="w-4 h-4" />
            </button>
        </div>
      </div>
    </>
  );
};


// --- MAIN PAGE COMPONENT ---
export default function NudgesPage() {
  const [briefings, setBriefings] = useState<CampaignBriefing[]>([]);
  const { clients, loading: appLoading } = useAppContext();

  useEffect(() => {
    if (appLoading) return;
    const fetchPageData = async () => {
      try {
        const res = await fetch('http://localhost:8001/nudges');
        if (!res.ok) throw new Error("Failed to fetch page data");
        const briefingsData = await res.json();
        setBriefings(briefingsData);
      } catch (error) {
        console.error("Failed to fetch page data:", error);
      }
    };
    fetchPageData();
  }, [appLoading]);

  const updateBriefing = (updatedBriefing: CampaignBriefing) => {
    setBriefings(briefings.map(b => b.id === updatedBriefing.id ? updatedBriefing : b));
  };
  
  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-[320px_1fr] lg:grid-cols-[320px_1fr_340px] bg-brand-dark text-brand-text-main font-sans">
      <aside className="bg-white/5 border-r border-white/10 p-4 flex flex-col gap-6">
          <Link href="/dashboard"><Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority /></Link>
        <nav className="space-y-1.5 mt-10">
          <Link href="/dashboard" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
            <MessageCircleHeart className="w-5 h-5" /> All Conversations
          </Link>
          <Link href="/nudges" className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold">
            <Zap className="w-5 h-5" /> AI Nudges
          </Link>
        </nav>
      </aside>
      <main className="flex flex-col p-8 overflow-y-auto">
        <h1 className="text-3xl font-bold text-white mb-2">AI Campaign Briefings</h1>
        <p className="text-brand-text-muted mb-8">Here are the latest opportunities the AI has identified for you.</p>
        <div className="space-y-8 max-w-4xl mx-auto w-full">
          {briefings.length > 0 ? (
            briefings.map(briefing => (
              <CampaignBriefingCard 
                key={briefing.id} 
                briefing={briefing} 
                allClients={clients} 
                onUpdate={updateBriefing} 
              />
            ))
          ) : (
            <div className="text-center py-20 bg-white/5 rounded-2xl">
              <Sparkles className="mx-auto w-16 h-16 text-brand-text-muted/50 mb-4" />
              <h3 className="text-xl font-bold text-white">All Clear!</h3>
              <p className="text-brand-text-muted">The AI is scanning your market for opportunities. New briefings will appear here.</p>
            </div>
          )}
        </div>
      </main>
      <aside className="bg-white/5 border-l border-white/10 p-6 hidden lg:flex"></aside>
    </div>
  );
}