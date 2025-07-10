// frontend/app/(main)/community/page.tsx
// DEFINITIVE FIX: Adds a conditional prompt to allow users who skipped
// the Google import during onboarding to perform it later.

'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAppContext } from '@/context/AppContext';
import { Users, Filter, Plus, UserCheck, UserX, MessageSquare, Bot, Mail } from 'lucide-react';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar';

const GoogleImportPrompt = () => {
    const { api, token } = useAppContext();
    const [isLoading, setIsLoading] = useState(false);

    const handleGoogleImport = async () => {
        setIsLoading(true);
        if (!token) {
            console.error("Authentication token not found.");
            setIsLoading(false);
            return;
        }
        try {
            const response = await api.get(`/api/auth/google-oauth-url?state=${token}`);
            if (response.auth_url) {
                window.location.href = response.auth_url;
            } else {
                throw new Error("Could not retrieve Google authentication URL.");
            }
        } catch (err) {
            console.error("Failed to start Google import:", err);
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-white/5 border border-dashed border-white/20 p-6 rounded-xl mb-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
                <h3 className="font-bold text-white text-lg flex items-center gap-2"><Bot size={20} /> Unlock Your Full Network</h3>
                <p className="text-brand-text-muted text-sm mt-1">Import contacts from Google to let your AI find every hidden opportunity.</p>
            </div>
            <button 
                onClick={handleGoogleImport} 
                disabled={isLoading} 
                className="w-full md:w-auto flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-semibold bg-primary-action text-brand-dark rounded-md hover:brightness-110 flex-shrink-0 transition-opacity disabled:opacity-50"
            >
                {isLoading ? 'Redirecting...' : <><Mail size={16} /> Import from Google</>}
            </button>
        </div>
    );
};

type CommunityMember = { client_id: string; full_name: string; user_tags: string[]; ai_tags?: string[]; last_interaction_days: number | null; health_score: number; };
const HealthBar = ({ score }: { score: number }) => {
  const getColor = () => {
    if (score > 70) return 'bg-green-500'; if (score > 40) return 'bg-yellow-500'; return 'bg-red-500';
  };
  return <div className="w-full bg-white/10 rounded-full h-1.5 mt-2"><div className={`h-1.5 rounded-full ${getColor()}`} style={{ width: `${score}%` }} /></div>;
};
const CommunityCard = ({ member }: { member: CommunityMember }) => (
  <Link href={`/conversations/${member.client_id}`} className="block bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 hover:border-white/20 transition-all duration-200 animate-in fade-in-0 zoom-in-95">
    <div className="flex flex-col h-full">
      <div className="flex-grow">
        <h3 className="font-bold text-brand-text-main">{member.full_name}</h3>
        <p className="text-xs text-brand-text-muted mt-1">{member.last_interaction_days !== null ? `Last contact: ${member.last_interaction_days} days ago` : 'No interactions yet'}</p>
        <HealthBar score={member.health_score} />
      </div>
      <div className="mt-4 flex flex-wrap gap-1.5">{member.user_tags.slice(0, 3).map(tag => <span key={tag} className="text-xs font-semibold bg-primary-action/20 text-brand-accent px-2 py-0.5 rounded-full">{tag}</span>)}</div>
    </div>
  </Link>
);

export default function CommunityPage() {
  const { api, user } = useAppContext();
  const [community, setCommunity] = useState<CommunityMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCommunityData = useCallback(async (searchQuery = '') => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (searchQuery.trim()) {
        data = await api.post('/api/clients/search', { natural_language_query: searchQuery });
        data = data.map((client: any) => ({ ...client, client_id: client.id, health_score: 50, last_interaction_days: null }));
      } else {
        data = await api.get('/api/community');
      }
      setCommunity(data);
    } catch (err: any) {
      setError(err.message || "Failed to load data.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchCommunityData();
  }, [fetchCommunityData]);

  const showImportPrompt = user && user.onboarding_complete && !user.onboarding_state?.google_sync_complete;

  const stats = {
    total: community.length,
    engaged: community.filter(c => c.health_score > 70).length,
    atRisk: community.filter(c => c.health_score <= 40).length,
  };

  return (
    <main className="flex-1 overflow-y-auto p-6 md:p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3"><Users size={32} />Community</h1>
        <p className="text-brand-text-muted mt-1">A strategic overview of your entire client audience.</p>
      </header>
      
      {showImportPrompt && <GoogleImportPrompt />}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white/5 p-4 rounded-lg flex items-center gap-4"><Users size={24} className="text-brand-accent" /><div><p className="text-2xl font-bold">{stats.total}</p><p className="text-sm text-brand-text-muted">Total Contacts</p></div></div>
        <div className="bg-white/5 p-4 rounded-lg flex items-center gap-4"><UserCheck size={24} className="text-green-500" /><div><p className="text-2xl font-bold">{stats.engaged}</p><p className="text-sm text-brand-text-muted">Engaged</p></div></div>
        <div className="bg-white/5 p-4 rounded-lg flex items-center gap-4"><UserX size={24} className="text-red-500" /><div><p className="text-2xl font-bold">{stats.atRisk}</p><p className="text-sm text-brand-text-muted">At Risk</p></div></div>
      </div>

      <div className="flex justify-between items-center mb-6 gap-4">
        <MagicSearchBar onSearch={fetchCommunityData} isLoading={loading} className="flex-grow" placeholder="e.g., Clients who bought over 5 years ago..."/>
        <button className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-primary-action text-brand-dark rounded-md hover:brightness-110 flex-shrink-0"><Plus size={16} /> Add Contact</button>
      </div>

      {loading && !community.length ? (<div className="p-8 text-center">Loading Community...</div>)
       : error ? (<div className="p-8 text-center text-red-400">Error: {error}</div>)
       : community.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {community.map(member => <CommunityCard key={member.client_id} member={member} />)}
        </div>
      ) : (
        <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
          <MessageSquare size={48} className="mx-auto text-brand-text-muted" />
          <h3 className="mt-4 text-xl font-bold">No Matching Clients Found</h3>
          <p className="text-brand-text-muted">Try clearing your search or adding new contacts.</p>
        </div>
      )}
    </main>
  );
}