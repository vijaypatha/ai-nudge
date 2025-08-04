// frontend/components/nudges/InstantNudgeView.tsx
'use client';

import { useState, useEffect, useCallback, useMemo, FC } from 'react';
import { useAppContext, Client } from '@/context/AppContext';
import { MagicSearchBar } from '@/components/ui/MagicSearchBar';
import { TagFilter } from '@/components/ui/TagFilter';
import { Avatar } from '@/components/ui/Avatar';
import { Loader2, Bot, Send, Calendar, Users } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
// --- FIX: Import the timezone detection utility ---
import { detectUserTimezone } from '../../utils/timezone';


interface InstantNudgeViewProps {
    clients: Client[];
    onScheduleSuccess: () => void;
}

export const InstantNudgeView: FC<InstantNudgeViewProps> = ({ clients, onScheduleSuccess }) => {
    const { api, user } = useAppContext();

    const [filteredClients, setFilteredClients] = useState<Client[]>(clients);
    const [selectedClients, setSelectedClients] = useState<Set<string>>(new Set());
    const [message, setMessage] = useState('');
    const [topic, setTopic] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [isDrafting, setIsDrafting] = useState(false);

    const [searchQuery, setSearchQuery] = useState('');
    const [filterTags, setFilterTags] = useState<string[]>([]);
    const [scheduleDateTime, setScheduleDateTime] = useState('');
    const [isScheduling, setIsScheduling] = useState(false);

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

    // --- DEFINITIVE FIX IS HERE ---
    const handleScheduleInstantNudge = async () => {
        if (selectedClients.size === 0 || !message.trim() || !scheduleDateTime.trim()) {
            alert("Please select recipients, write a message, and pick a future date and time.");
            return;
        }
        setIsScheduling(true);

        const scheduledDateTimeObj = new Date(scheduleDateTime);
        if (scheduledDateTimeObj <= new Date()) {
            alert("Please select a future date and time for scheduling.");
            setIsScheduling(false);
            return;
        }
        
        try {
            // FIX: Get the user's timezone from context, with a fallback to browser detection.
            // The backend /bulk endpoint requires this field.
            const userTimezone = user?.timezone || detectUserTimezone();

            await api.post('/api/scheduled-messages/bulk', {
                client_ids: Array.from(selectedClients),
                content: message,
                scheduled_at_local: scheduledDateTimeObj,
                timezone: userTimezone, // FIX: Added the required timezone field
            });

            // Changed alert to be more accurate based on backend logic.
            alert(`Successfully scheduled message for ${selectedClients.size} client(s).`);
            setSelectedClients(new Set());
            setMessage('');
            setTopic('');
            setScheduleDateTime('');
            onScheduleSuccess();
        } catch (error) {
            console.error("Failed to bulk schedule nudge:", error);
            alert("An error occurred while scheduling the messages. Please check the console.");
        } finally {
            setIsScheduling(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
            <motion.section 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="lg:col-span-2"
            >
                <div className="flex items-center gap-4 mb-4">
                    <span className="flex items-center justify-center w-10 h-10 rounded-full bg-primary-action text-brand-dark font-bold text-lg">1</span>
                    <h2 className="text-2xl font-bold">Target Your Audience</h2>
                </div>
                <div className="p-6 bg-brand-primary border border-white/10 rounded-xl space-y-5">
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted mb-2 block">Natural Language Audience Builder ✨</label>
                        <MagicSearchBar onSearch={setSearchQuery} isLoading={isSearching} placeholder="e.g., My clients who are avid golfers..." />
                    </div>

                    <TagFilter allTags={allTags} onFilterChange={setFilterTags} />

                    <div className="border border-white/10 rounded-lg">
                        <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-primary/80 backdrop-blur-sm z-10">
                            <label className="flex items-center gap-3 text-sm font-medium">
                                <input type="checkbox" className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent focus:ring-offset-0" checked={selectedClients.size > 0 && selectedClients.size === filteredClients.length && filteredClients.length > 0} onChange={handleSelectAll} />
                                Select All Filtered ({selectedClients.size}/{filteredClients.length})
                            </label>
                        </div>
                        <div className="max-h-64 overflow-y-auto p-2">
                            {isSearching ? (
                                <div className="flex justify-center items-center p-8 text-brand-text-muted"><Loader2 className="animate-spin mr-2" /> Searching...</div>
                            ) : filteredClients.length === 0 ? (
                                <div className="flex flex-col text-center items-center p-8 text-brand-text-muted">
                                    <Users size={32} className="mb-2"/>
                                    <p className="font-semibold">No Clients Found</p>
                                    <p className="text-sm">Try adjusting your search or filters.</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                    {filteredClients.map(client => (
                                        <div key={client.id} className="relative">
                                            <input type="checkbox" id={`client-${client.id}`} className="absolute opacity-0 w-full h-full cursor-pointer" checked={selectedClients.has(client.id)} onChange={() => handleSelectClient(client.id)} />
                                            <label htmlFor={`client-${client.id}`} className={clsx("flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all", selectedClients.has(client.id) ? "bg-primary-action/20 border-primary-action" : "bg-white/5 border-transparent hover:bg-white/10")}>
                                                <div className={clsx("w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center", selectedClients.has(client.id) ? "bg-primary-action border-primary-action" : "border-white/20")}>
                                                    {selectedClients.has(client.id) && <Send size={12} className="text-brand-dark" />}
                                                </div>
                                                <Avatar name={client.full_name} className="w-8 h-8 text-xs"/>
                                                <span className="font-medium truncate">{client.full_name}</span>
                                            </label>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </motion.section>
            <motion.section 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="lg:col-span-3"
            >
                <div className="flex items-center gap-4 mb-4">
                    <span className="flex items-center justify-center w-10 h-10 rounded-full bg-primary-action text-brand-dark font-bold text-lg">2</span>
                    <h2 className="text-2xl font-bold">Draft Your Nudge</h2>
                </div>
                <div className="p-6 bg-brand-primary border border-white/10 rounded-xl space-y-5">
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted" htmlFor="topic">Topic / Goal (for AI draft)</label>
                        <input id="topic" type="text" value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g., End of quarter market update" className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"/>
                    </div>
                    <div>
                        <label className="text-sm font-semibold text-brand-text-muted" htmlFor="message">Message</label>
                        <textarea id="message" rows={6} value={message} onChange={e => setMessage(e.target.value)} placeholder="Click 'Draft with AI' or write your own message..." className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3"></textarea>
                    </div>
                    <div className="flex flex-col gap-4 pt-2">
                        <button onClick={handleDraftWithAI} disabled={isDrafting || !topic.trim()} className="flex items-center justify-center gap-2 p-3 bg-white/10 rounded-lg font-semibold hover:bg-white/20 disabled:opacity-50 w-full transition-colors">
                            {isDrafting ? <Loader2 size={20} className="animate-spin" /> : <Bot size={20} />}
                            {isDrafting ? 'Drafting...' : 'Draft with AI'}
                        </button>
                        
                        <div className="h-px bg-white/10"></div>

                        <AnimatePresence mode="wait">
                        {scheduleDateTime ? (
                            <motion.div key="schedule" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                                <label className="text-sm font-semibold text-brand-text-muted">Schedule for later</label>
                                <input 
                                    type="datetime-local" 
                                    value={scheduleDateTime}
                                    onChange={e => setScheduleDateTime(e.target.value)}
                                    className="p-3 w-full bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-cyan-500"
                                />
                                <p className="text-xs text-gray-400">
                                    This message will be sent to clients at the specified time in your local timezone ({user?.timezone || detectUserTimezone()}).
                                </p>
                                <div className="grid grid-cols-2 gap-3">
                                    <button onClick={() => setScheduleDateTime('')} className="p-3 bg-white/10 rounded-lg font-semibold hover:bg-white/20 w-full">Cancel</button>
                                    <button onClick={handleScheduleInstantNudge} disabled={isScheduling || selectedClients.size === 0 || !message.trim()} className="p-3 bg-cyan-500 text-brand-dark rounded-lg font-semibold hover:bg-cyan-400 disabled:opacity-50 whitespace-nowrap w-full flex items-center justify-center gap-2">
                                        {isScheduling ? <Loader2 size={20} className="animate-spin" /> : <Calendar size={20} />}
                                        {isScheduling ? 'Scheduling...' : `Confirm (${selectedClients.size})`}
                                    </button>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div key="send" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-2 gap-3">
                                <button onClick={() => {
                                    const futureDate = new Date(Date.now() + 30 * 60 * 1000);
                                    const localISOString = new Date(futureDate.getTime() - (futureDate.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
                                    setScheduleDateTime(localISOString);
                                }} className="p-3 bg-white/10 rounded-lg font-semibold hover:bg-white/20 disabled:opacity-50 w-full flex items-center justify-center gap-2">
                                    <Calendar size={20} /> Schedule
                                </button>
                                <button onClick={handleSendInstantNudge} disabled={isSending || selectedClients.size === 0 || !message.trim()} className="p-3 bg-primary-action text-brand-dark rounded-lg font-semibold hover:brightness-110 disabled:opacity-50 w-full flex items-center justify-center gap-2">
                                    {isSending ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                                    {isSending ? 'Sending...' : `Send Now (${selectedClients.size})`}
                                </button>
                            </motion.div>
                        )}
                        </AnimatePresence>
                    </div>
                </div>
            </motion.section>
        </div>
    );
};