// frontend/app/(main)/community/page.tsx
// --- MODIFIED ---
// Purpose: Integrates the new TagFilter component and updates data fetching
// to support combined natural language and tag-based filtering.

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAppContext, Client } from '@/context/AppContext';
import { Users, Plus, UserCheck, UserX, MessageSquare } from 'lucide-react';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar';
import { TagFilter } from '@/components/ui/TagFilter'; // NEW IMPORT
import { AddContactModal } from '@/components/modals/AddContactModal';
import { EditContactModal } from '@/components/modals/EditContactModal';
import Confetti from 'react-confetti';
import { ACTIVE_THEME } from '@/utils/theme';

// --- HELPER TYPES & COMPONENTS (Unchanged) ---

type CommunityMember = {
    client_id: string;
    full_name: string;
    user_tags: string[];
    ai_tags?: string[];
    last_interaction_days: number | null;
    health_score: number;
};

const GoogleImportPrompt = () => {
    // ... (Component implementation is unchanged)
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
                <h3 className="font-bold text-white text-lg flex items-center gap-2">
                    <div className="flex items-center justify-center w-6 h-6 bg-white rounded shadow-sm">
                        <svg className="w-4 h-4" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                    </div>
                    Unlock Your Full Network
                </h3>
                <p className="text-brand-text-muted text-sm mt-1">Import contacts from Google to let your AI find every hidden opportunity.</p>
            </div>
            <button 
                onClick={handleGoogleImport} 
                disabled={isLoading} 
                className="w-full md:w-auto flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-semibold bg-primary-action text-brand-dark rounded-md hover:brightness-110 flex-shrink-0 transition-opacity disabled:opacity-50"
            >
                {isLoading ? 'Redirecting...' : <>
                    <div className="flex items-center justify-center w-4 h-4 bg-white rounded shadow-sm">
                        <svg className="w-3 h-3" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                    </div>
                    Import from Google
                </>}
            </button>
        </div>
    );
};

const HealthBar = ({ score }: { score: number }) => {
  const getColor = () => {
    if (score > 70) return 'bg-green-500'; if (score > 40) return 'bg-yellow-500'; return 'bg-red-500';
  };
  return <div className="w-full bg-white/10 rounded-full h-1.5 mt-2"><div className={`h-1.5 rounded-full ${getColor()}`} style={{ width: `${score}%` }} /></div>;
};

const CommunityCard = ({ member, onEdit }: { member: CommunityMember; onEdit: (member: CommunityMember) => void }) => {
  const router = useRouter();
  
  const handleCardClick = (e: React.MouseEvent) => {
    // Check if the click was on the edit button or its children
    const target = e.target as HTMLElement;
    if (target.closest('button[title="Edit contact"]')) {
      return; // Don't navigate if edit button was clicked
    }
    
    // Navigate to conversation page
    router.push(`/conversations/${member.client_id}`);
  };

  return (
    <div 
      className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 hover:border-white/20 transition-all duration-200 animate-in fade-in-0 zoom-in-95 relative group cursor-pointer"
      onClick={handleCardClick}
    >
      {/* Edit button positioned in top-right corner */}
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onEdit(member);
        }}
        className="absolute top-2 right-2 z-50 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-white/10 rounded text-brand-text-muted hover:text-white"
        title="Edit contact"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      </button>
      
      {/* Card content */}
      <div className="flex flex-col h-full">
        <div className="flex-grow">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-bold text-brand-text-main">{member.full_name}</h3>
            {/* Empty space to maintain layout */}
            <div className="w-6 h-6"></div>
          </div>
          <p className="text-xs text-brand-text-muted mt-1">{member.last_interaction_days !== null ? `Last contact: ${member.last_interaction_days} days ago` : 'No interactions yet'}</p>
          <HealthBar score={member.health_score} />
        </div>
        <div className="mt-4 flex flex-wrap gap-1.5">
          {[...member.user_tags, ...(member.ai_tags || [])].slice(0, 3).map(tag => <span key={tag} className="text-xs font-semibold bg-primary-action/20 text-brand-accent px-2 py-0.5 rounded-full">{tag}</span>)}
        </div>
      </div>
    </div>
  );
};


// --- MAIN PAGE COMPONENT ---

export default function CommunityPage() {
  const { api, user } = useAppContext();
  const [community, setCommunity] = useState<CommunityMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for search and filter values
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTags, setFilterTags] = useState<string[]>([]);
  
  // State to hold the complete, unfiltered list of clients
  const [allClients, setAllClients] = useState<CommunityMember[]>([]);
  
  // State for edit contact modal
  const [isEditContactModalOpen, setIsEditContactModalOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<CommunityMember | null>(null);
  
  // State for the Add Contact modal
  const [isAddContactModalOpen, setIsAddContactModalOpen] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  // Memoize all unique tags from the full client list for the filter component.
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    allClients.forEach(client => {
      client.user_tags?.forEach(tag => tags.add(tag));
      client.ai_tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [allClients]);

  // Fetch the full community list on initial load to populate the tag filter.
  useEffect(() => {
    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const data = await api.get('/api/community');
            setAllClients(data);
            setCommunity(data); // Initially, the displayed community is the full list.
        } catch (err: any) {
            setError(err.message || "Failed to load initial data.");
        } finally {
            setLoading(false);
        }
    };
    fetchInitialData();
  }, [api]);

  // This function now handles all filtering logic.
  const fetchFilteredData = useCallback(async () => {
    // Prevent running during the initial data load.
    if (loading && allClients.length === 0) return;

    setLoading(true);
    setError(null);

    const hasQuery = searchQuery.trim().length > 0;
    const hasTags = filterTags.length > 0;

    // If no filters are active, display the full client list and exit.
    if (!hasQuery && !hasTags) {
        setCommunity(allClients);
        setLoading(false);
        return;
    }

    try {
      // The /api/clients/search endpoint handles combined queries.
      const payload: { natural_language_query?: string; tags?: string[] } = {};
      if (hasQuery) payload.natural_language_query = searchQuery;
      if (hasTags) payload.tags = filterTags;
      
      const results: Client[] = await api.post('/api/clients/search', payload);
      
      // The search endpoint returns basic Client objects. We need to enrich them
      // with the health metrics for display in the Community view.
      const enrichedResults = results.map((client: Client) => {
        const fullClientData = allClients.find(c => c.client_id === client.id);
        return fullClientData || { 
            ...client, 
            client_id: client.id, 
            health_score: 50, // Default fallback score
            last_interaction_days: null 
        };
      });

      setCommunity(enrichedResults);

    } catch (err: any) {
      setError(err.message || "Failed to load filtered data.");
      setCommunity([]);
    } finally {
      setLoading(false);
    }
  }, [api, searchQuery, filterTags, allClients, loading]);

  // Use a single debounced useEffect to trigger the search/filter action.
  useEffect(() => {
    const handler = setTimeout(() => {
      // Avoid triggering on initial render before data is loaded.
      if (!loading) {
        fetchFilteredData();
      }
    }, 500); // Debounce input to avoid excessive API calls
    return () => clearTimeout(handler);
  }, [searchQuery, filterTags, loading, fetchFilteredData]);
  
  // Handler for when a contact is successfully added
  const handleContactAdded = useCallback(async () => {
    // Refresh the community data to include the new contact
    setLoading(true);
    try {
      const data = await api.get('/api/community');
      setAllClients(data);
      setCommunity(data);
    } catch (err: any) {
      setError(err.message || "Failed to refresh data after adding contact.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  // Handler for when a contact is successfully updated
  const handleContactUpdated = useCallback(async () => {
    // Refresh the community data to reflect the updated contact
    setLoading(true);
    try {
      const data = await api.get('/api/community');
      setAllClients(data);
      setCommunity(data);
    } catch (err: any) {
      setError(err.message || "Failed to refresh data after updating contact.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  // Handler for when a contact is successfully deleted
  const handleContactDeleted = useCallback(async () => {
    // Refresh the community data to reflect the deleted contact
    setLoading(true);
    try {
      const data = await api.get('/api/community');
      setAllClients(data);
      setCommunity(data);
    } catch (err: any) {
      setError(err.message || "Failed to refresh data after deleting contact.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  // Handler for opening the edit contact modal
  const handleEditContact = useCallback((client: CommunityMember) => {
    setSelectedClient(client);
    setIsEditContactModalOpen(true);
  }, []);
  
  const showImportPrompt = user && user.onboarding_complete && !user.onboarding_state?.google_sync_complete;

  const stats = {
    total: community.length,
    engaged: community.filter(c => c.health_score > 70).length,
    atRisk: community.filter(c => c.health_score <= 40).length,
  };

  useEffect(() => {
      const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
      window.addEventListener('resize', handleResize);
      handleResize();
      return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleShowConfetti = useCallback(() => {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 7000);
  }, []);

  return (
    <main className="flex-1 overflow-y-auto p-6 md:p-8">
      {showConfetti && (
          <Confetti
              width={windowSize.width}
              height={windowSize.height}
              recycle={false}
              numberOfPieces={600}
              tweenDuration={7000}
              colors={[
                  ACTIVE_THEME.primary.from, 
                  ACTIVE_THEME.primary.to, 
                  ACTIVE_THEME.accent, 
                  ACTIVE_THEME.action,
                  '#ffffff'
              ]}
          />
      )}
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
        {/* MagicSearchBar now updates state, which triggers the debounced useEffect */}
        <MagicSearchBar onSearch={setSearchQuery} isLoading={loading} className="flex-grow" placeholder="e.g., Clients who bought over 5 years ago..."/>
        <button 
          onClick={() => setIsAddContactModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-primary-action text-brand-dark rounded-md hover:brightness-110 flex-shrink-0"
        >
          <Plus size={16} /> Add Contact
        </button>
      </div>
      
      {/* NEW: The TagFilter component is now rendered here */}
      <TagFilter allTags={allTags} onFilterChange={setFilterTags} />

      {loading && !community.length ? (<div className="p-8 text-center text-brand-text-muted">Loading Community...</div>)
       : error ? (<div className="p-8 text-center text-red-400">Error: {error}</div>)
       : community.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {community.map(member => <CommunityCard key={member.client_id} member={member} onEdit={handleEditContact} />)}
        </div>
      ) : (
        <div className="text-center py-20 border-2 border-dashed border-white/10 rounded-xl">
          <MessageSquare size={48} className="mx-auto text-brand-text-muted" />
          <h3 className="mt-4 text-xl font-bold">No Matching Clients Found</h3>
          <p className="text-brand-text-muted">Try clearing your search or adjusting your filters.</p>
        </div>
      )}
      
      {/* Add Contact Modal */}
      <AddContactModal 
        isOpen={isAddContactModalOpen}
        onClose={() => setIsAddContactModalOpen(false)}
        onContactAdded={handleContactAdded}
        onShowConfetti={handleShowConfetti}
      />
      
      {/* Edit Contact Modal */}
      <EditContactModal 
        isOpen={isEditContactModalOpen}
        onClose={() => {
          setIsEditContactModalOpen(false);
          setSelectedClient(null);
        }}
        client={selectedClient}
        onContactUpdated={handleContactUpdated}
        onContactDeleted={handleContactDeleted}
      />
    </main>
  );
}
