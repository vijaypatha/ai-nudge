// ---
// File Path: frontend/app/nudges/ManageAudienceModal.tsx
// Purpose: A reusable modal component for searching, filtering, and managing a client audience.
// This version is CORRECTED to fix the initial client list loading and to handle async save operations.
// ---

'use client'; 

import { useState, useEffect, useMemo } from 'react';
import { X, Search } from 'lucide-react';
import clsx from 'clsx';
import type { Client } from '../../context/AppContext';

// --- Helper Components ---
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

// --- Main Component ---
interface ManageAudienceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newAudience: Client[]) => Promise<void>;
  allClients: Client[]; // Although we fetch, passing allClients helps get unique tags without another API call.
  initialSelectedClientIds: Set<string>;
}

export const ManageAudienceModal = ({
  isOpen,
  onClose,
  onSave,
  allClients,
  initialSelectedClientIds,
}: ManageAudienceModalProps) => {
  // --- State Management ---
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [filteredClients, setFilteredClients] = useState<Client[]>([]); // Start with an empty list
  const [selectedClientIds, setSelectedClientIds] = useState<Set<string>>(initialSelectedClientIds);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- Derived Data ---
  const uniqueTags = useMemo(() => {
    const allTags = new Set<string>();
    allClients.forEach((client) => {
      client.tags.forEach((tag) => allTags.add(tag));
    });
    return Array.from(allTags).sort();
  }, [allClients]);

  // --- Effects ---
  // Effect to reset selection state when the modal is opened.
  useEffect(() => {
    if (isOpen) {
      setSelectedClientIds(initialSelectedClientIds);
      setIsSaving(false);
      setError(null);
    }
  }, [isOpen, initialSelectedClientIds]);

  // Effect to perform the client search when the query or tags change, or when the modal opens.
  useEffect(() => {
    // Do not run this effect if the modal is closed.
    if (!isOpen) {
      return;
    }
    
    // Using a debounce timer to prevent excessive API calls while typing.
    const handler = setTimeout(() => {
      const performSearch = async () => {
        setIsLoading(true);
        setError(null);
        try {
          // Always fetch from the backend. The backend returns all clients if query/tags are empty.
          const response = await fetch('http://localhost:8001/clients/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              natural_language_query: searchQuery || null,
              tags: activeTags.size > 0 ? Array.from(activeTags) : null,
            }),
          });
          if (!response.ok) {
            throw new Error('Failed to fetch clients.');
          }
          const data: Client[] = await response.json();
          setFilteredClients(data);
        } catch (err: any) {
          setError(err.message);
          setFilteredClients([]);
        } finally {
          setIsLoading(false);
        }
      };
      performSearch();
    }, 150); // Short delay for responsiveness

    // Cleanup function to cancel the timeout if the effect re-runs.
    return () => clearTimeout(handler);
  }, [searchQuery, activeTags, isOpen]); // Re-run whenever search terms change or modal opens.

  // --- Event Handlers ---
  const handleTagClick = (tag: string) => {
    const newTags = new Set(activeTags);
    if (newTags.has(tag)) newTags.delete(tag);
    else newTags.add(tag);
    setActiveTags(newTags);
  };

  const handleSelectClient = (clientId: string) => {
    const newSelection = new Set(selectedClientIds);
    if (newSelection.has(clientId)) newSelection.delete(clientId);
    else newSelection.add(clientId);
    setSelectedClientIds(newSelection);
  };
  
  const handleSelectAllFiltered = () => {
      const allFilteredIds = new Set(filteredClients.map(c => c.id));
      const isAllSelected = filteredClients.length > 0 && filteredClients.every(c => selectedClientIds.has(c.id));
      if (isAllSelected) {
          const newSelection = new Set(selectedClientIds);
          allFilteredIds.forEach(id => newSelection.delete(id));
          setSelectedClientIds(newSelection);
      } else {
          const newSelection = new Set(selectedClientIds);
          allFilteredIds.forEach(id => newSelection.add(id));
          setSelectedClientIds(newSelection);
      }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    // We need the full Client objects for the parent, but we can get them from the currently filtered list
    // for efficiency, falling back to allClients if needed.
    const masterClientList = allClients.length > 0 ? allClients : filteredClients;
    const selectedClientObjects = masterClientList.filter(c => selectedClientIds.has(c.id));

    try {
      await onSave(selectedClientObjects);
      onClose();
    } catch (err) {
      console.error("Failed to save audience:", err);
      setError("Failed to save audience. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const isAllFilteredSelected = filteredClients.length > 0 && filteredClients.every(c => selectedClientIds.has(c.id));

  // --- Render ---
  return (
    <div className="fixed inset-0 bg-brand-dark/90 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-brand-dark-blue border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <header className="p-6 border-b border-white/10 flex justify-between items-center flex-shrink-0">
          <h2 className="text-2xl font-bold text-brand-text-main">Manage Audience</h2>
          <button onClick={onClose} className="text-brand-text-muted hover:text-white"><X size={24} /></button>
        </header>

        <div className="p-6 space-y-4 flex-shrink-0">
          <div className="relative">
            <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-brand-text-muted" />
            <input type="text" placeholder="AI Nudge Magic Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full bg-black/20 border border-white/20 rounded-lg p-3 pl-10 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"/>
          </div>
          <div className="flex flex-wrap gap-2">
            {uniqueTags.map((tag) => ( <button key={tag} onClick={() => handleTagClick(tag)} className={clsx('px-3 py-1.5 text-sm font-semibold rounded-full border transition-colors', activeTags.has(tag) ? 'bg-brand-accent text-brand-dark border-brand-accent' : 'bg-white/5 border-white/10 text-brand-text-muted hover:border-white/30')}> {tag} </button> ))}
          </div>
        </div>

        <div className="px-6 pb-2 flex-grow overflow-y-auto">
          <div className="border border-white/10 rounded-lg">
            <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-dark-blue/80 backdrop-blur-sm">
                <label className="flex items-center gap-3 text-sm font-semibold cursor-pointer text-white">
                    <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent focus:ring-offset-brand-dark-blue" checked={isAllFilteredSelected} onChange={handleSelectAllFiltered}/>
                    Select All ({selectedClientIds.size} selected)
                </label>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {isLoading ? (<p className="p-4 text-center text-brand-text-muted">Searching...</p>) 
              : error && filteredClients.length === 0 ? (<p className="p-4 text-center text-red-400">{error}</p>) 
              : !error && filteredClients.length === 0 ? (<p className="p-4 text-center text-brand-text-muted">No clients found.</p>) 
              : (
                filteredClients.map((client) => (
                  <div key={client.id} className="border-b border-white/10 last:border-b-0">
                    <label className="flex items-center gap-3 p-3 hover:bg-white/5 cursor-pointer">
                      <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClientIds.has(client.id)} onChange={() => handleSelectClient(client.id)}/>
                      <Avatar name={client.full_name} className="w-8 h-8 text-xs" />
                      <span className="text-base text-brand-text-main">{client.full_name}</span>
                    </label>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <footer className="p-6 border-t border-white/10 flex justify-end items-center gap-4 flex-shrink-0">
           {/* Display save error here as well for better visibility */}
           {error && !isLoading && <p className="text-red-400 text-sm mr-auto">{error}</p>}
          <button onClick={onClose} className="px-5 py-2.5 font-semibold text-brand-text-muted hover:text-white">Cancel</button>
          <button onClick={handleSave} disabled={selectedClientIds.size === 0 || isSaving} className="px-6 py-2.5 bg-primary-action text-brand-dark font-bold rounded-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed w-48 text-center">
            {isSaving ? 'Saving...' : `Save Audience (${selectedClientIds.size})`}
          </button>
        </footer>
      </div>
    </div>
  );
};