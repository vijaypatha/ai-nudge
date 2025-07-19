// frontend/components/nudges/InstantNudgeView.tsx
// --- DEFINITIVE FIX ---
// Purpose: This component now receives a fresh list of clients via props,
// ensuring that the TagFilter has data and renders correctly.

'use client';

import { useState, useEffect, useCallback, useMemo, FC } from 'react';
import { useAppContext, Client } from '@/context/AppContext';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar';
import { TagFilter } from '@/components/ui/TagFilter';
import { Avatar } from '@/components/ui/Avatar';
import { Loader2, Bot, Send } from 'lucide-react';

// --- NEW: Define props interface ---
interface InstantNudgeViewProps {
    clients: Client[];
}

export const InstantNudgeView: FC<InstantNudgeViewProps> = ({ clients }) => {
    // --- MODIFIED: 'clients' now comes from props. Only 'api' is needed from context.
    const { api } = useAppContext();

    const [filteredClients, setFilteredClients] = useState<Client[]>(clients);
    const [selectedClients, setSelectedClients] = useState<Set<string>>(new Set());
    const [message, setMessage] = useState('');
    const [topic, setTopic] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [isDrafting, setIsDrafting] = useState(false);

    const [searchQuery, setSearchQuery] = useState('');
    const [filterTags, setFilterTags] = useState<string[]>([]);

    // --- NEW: useEffect to sync filtered clients when the props change ---
    useEffect(() => {
        setFilteredClients(clients);
    }, [clients]);

    const allTags = useMemo(() => {
        const tags = new Set<string>();
        clients.forEach(client => {
            client.user_tags?.forEach(tag => tags.add(tag));
            client.ai_tags?.forEach(tag => tags.add(tag));
        });
        return Array.from(tags).sort();
    }, [clients]);

    const handleAudienceSearch = useCallback(async () => {
        setIsSearching(true);
        const hasQuery = searchQuery.trim().length > 0;
        const hasTags = filterTags.length > 0;

        if (!hasQuery && !hasTags) {
            setFilteredClients(clients);
            setIsSearching(false);
            return;
        }

        try {
            const payload: { natural_language_query?: string; tags?: string[] } = {};
            if (hasQuery) payload.natural_language_query = searchQuery;
            if (hasTags) payload.tags = filterTags;

            const results = await api.post('/api/clients/search', payload);
            setFilteredClients(results);
        } catch (error) {
            console.error("Failed to search for clients:", error);
            setFilteredClients([]);
        } finally {
            setIsSearching(false);
        }
    }, [api, clients, searchQuery, filterTags]);

    useEffect(() => {
        const handler = setTimeout(() => {
            handleAudienceSearch();
        }, 500);
        return () => clearTimeout(handler);
    }, [searchQuery, filterTags, handleAudienceSearch]);


    const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked) {
            setSelectedClients(new Set(filteredClients.map(c => c.id)));
        } else {
            setSelectedClients(new Set());
        }
    };

    const handleSelectClient = (clientId: string) => {
        const newSelection = new Set(selectedClients);
        newSelection.has(clientId) ? newSelection.delete(clientId) : newSelection.add(clientId);
        setSelectedClients(newSelection);
    };

    const handleDraftWithAI = async () => {
        if (!topic.trim()) {
            alert("Please provide a topic or goal for the AI to draft a message.");
            return;
        }
        setIsDrafting(true);
        try {
            const response = await api.post('/api/campaigns/draft-instant-nudge', { topic });
            setMessage(response.draft);
        } catch (error) {
            console.error("Failed to draft with AI:", error);
            alert("There was an error generating the AI draft. Please try again.");
        } finally {
            setIsDrafting(false);
        }
    };

    const handleSendInstantNudge = async () => {
        if (selectedClients.size === 0 || !message.trim()) {
            alert("Please select at least one recipient and write a message.");
            return;
        }
        setIsSending(true);
        const recipients = Array.from(selectedClients);
        const sendPromises = recipients.map(clientId =>
            api.post('/api/campaigns/messages/send-now', { client_id: clientId, content: message })
        );
        try {
            await Promise.all(sendPromises);
            alert(`Successfully sent message to ${recipients.length} client(s).`);
            setSelectedClients(new Set());
            setMessage('');
            setTopic('');
        } catch (error) {
            console.error("Failed to send instant nudge:", error);
            alert("An error occurred while sending the message. Please check the console.");
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="space-y-8 max-w-4xl mx-auto">
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">1</span>
                    <h2 className="text-2xl font-bold">Target Your Audience</h2>
                </div>
                <div className="p-6 bg-brand-primary border border-white/10 rounded-xl space-y-4">
                    <label className="text-sm font-semibold text-brand-text-muted">Natural Language Audience Builder ✨</label>
                    <MagicSearchBar onSearch={setSearchQuery} isLoading={isSearching} placeholder="e.g., My clients who are avid golfers..." />

                    <TagFilter allTags={allTags} onFilterChange={setFilterTags} />

                    <div className="border border-white/10 rounded-lg max-h-64 overflow-y-auto">
                        <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-primary/80 backdrop-blur-sm">
                            <label className="flex items-center gap-3 text-sm">
                                <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" checked={selectedClients.size > 0 && selectedClients.size === filteredClients.length && filteredClients.length > 0} onChange={handleSelectAll} />
                                Select All Filtered ({selectedClients.size}/{filteredClients.length})
                            </label>
                        </div>
                        {isSearching ? (
                            <div className="flex justify-center items-center p-8 text-brand-text-muted"><Loader2 className="animate-spin mr-2" /> Searching...</div>
                        ) : filteredClients.map(client => (
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
                <div className="p-6 bg-brand-primary border border-white/10 rounded-xl space-y-4">
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted" htmlFor="topic">Topic / Goal (for AI draft)</label>
                        <input id="topic" type="text" value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g., End of quarter market update" className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"/>
                    </div>
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted" htmlFor="message">Message</label>
                        <textarea id="message" rows={5} value={message} onChange={e => setMessage(e.target.value)} placeholder="Click 'Draft with AI' or write your own message..." className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"></textarea>
                    </div>
                    <div className="flex flex-wrap items-center gap-4">
                        <button onClick={handleDraftWithAI} disabled={isDrafting || !topic.trim()} className="flex items-center gap-2 p-3 bg-white/10 rounded-md font-semibold hover:bg-white/20 disabled:opacity-50">
                            {isDrafting ? <Loader2 size={18} className="animate-spin" /> : <Bot size={18} />}
                            {isDrafting ? 'Drafting...' : 'Draft with AI'}
                        </button>
                        <button onClick={handleSendInstantNudge} disabled={isSending || selectedClients.size === 0 || !message.trim()} className="flex items-center gap-2 p-3 bg-primary-action text-brand-dark rounded-md font-semibold hover:brightness-110 disabled:opacity-50">
                            {isSending ? 'Sending...' : <><Send size={18} /> Send to {selectedClients.size} recipients</>}
                        </button>
                    </div>
                </div>
            </section>
        </div>
    );
};