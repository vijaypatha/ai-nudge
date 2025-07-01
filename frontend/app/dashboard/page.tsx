// File Path: frontend/app/dashboard/page.tsx
// --- UPDATED to use live backend APIs for conversations ---

'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import clsx from 'clsx';
import { useAppContext } from '../../context/AppContext';
import type { Client, Property, Message, Conversation, ScheduledMessage } from '../../context/AppContext';
import {
  MessageCircleHeart, Zap, Users, MessageSquare, Paperclip, Phone, Video,
  Sparkles, Search, Send, Calendar, Gift, Star, X, Edit2, Info, User as UserIcon, Menu
} from "lucide-react";


// --- Reusable Sub-Components (Preserved from original design) ---

const InfoCard = ({ title, children, className, onEdit }: { title: string, children: React.ReactNode, className?: string, onEdit?: () => void }) => (
  <div className={clsx("bg-white/5 border border-white/10 rounded-xl relative", className)}>
    <div className="flex justify-between items-center px-4 pt-4 pb-2">
      <h3 className="text-sm font-semibold text-brand-text-muted">{title}</h3>
      {onEdit && (
        <button onClick={onEdit} className="p-1 text-brand-text-muted hover:text-white opacity-50 hover:opacity-100 transition-opacity" title="Edit Intel">
          <Edit2 size={14} />
        </button>
      )}
    </div>
    <div className="p-4 pt-0"> {children} </div>
  </div>
);

const Avatar = ({ name, className }: { name: string, className?: string }) => {
  const initials = name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
  return (<div className={clsx("flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none", className)}> {initials} </div>);
};

const EditMessageModal = ({ isOpen, onClose, message, onSave }: { isOpen: boolean; onClose: () => void; message: ScheduledMessage | null; onSave: (updatedMessage: ScheduledMessage) => void; }) => {
  const [content, setContent] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  useEffect(() => {
    if (message) {
      setContent(message.content);
      setScheduledAt(new Date(message.scheduled_at).toISOString().split('T')[0]);
    }
  }, [message]);
  if (!isOpen || !message) return null;
  const handleSave = async () => {
    const res = await fetch(`http://localhost:8001/scheduled-messages/${message.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, scheduled_at: new Date(scheduledAt).toISOString() })
    });
    if (res.ok) {
      const updatedMessage = await res.json();
      onSave(updatedMessage);
      onClose();
    } else {
      alert("Failed to save changes.");
    }
  };
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-brand-dark border border-white/10 rounded-2xl w-full max-w-2xl flex flex-col shadow-2xl">
        <header className="p-6 border-b border-white/10 flex justify-between items-center"><h2 className="text-xl font-bold text-white">Edit Scheduled Message</h2><button onClick={onClose} className="p-2 rounded-full hover:bg-white/10"><X size={20} /></button></header>
        <main className="p-6 space-y-4">
          <div><label className="text-sm font-semibold text-brand-text-muted mb-2 block">Scheduled Date</label><input type="date" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white" /></div>
          <div><label className="text-sm font-semibold text-brand-text-muted mb-2 block">Message Content</label><textarea value={content} onChange={e => setContent(e.target.value)} rows={6} className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent" /></div>
        </main>
        <footer className="p-6 border-t border-white/10 flex justify-end gap-4"><button onClick={onClose} className="px-5 py-2.5 text-sm font-semibold bg-white/10 hover:bg-white/20 rounded-md">Cancel</button><button onClick={handleSave} className="px-5 py-2.5 text-sm font-semibold bg-primary-action text-brand-dark hover:brightness-110 rounded-md">Save Changes</button></footer>
      </div>
    </div>
  );
};

const ClientIntelCard = ({ client, onUpdate, onReplan }: { client: Client | undefined, onUpdate: (updatedClient: Client) => void, onReplan: () => void }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [notes, setNotes] = useState('');
  const [showReplanPrompt, setShowReplanPrompt] = useState(false);
  useEffect(() => { if (client) { setNotes(client.preferences?.notes?.join('\n') || ''); } }, [client]);
  if (!client) return null;
  const handleSave = async () => {
    const updatedPreferences = { ...client.preferences, notes: notes.split('\n').filter(n => n.trim()) };
    const res = await fetch(`http://localhost:8001/clients/${client.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ preferences: updatedPreferences }) });
    if (res.ok) {
      const updatedClient = await res.json();
      onUpdate(updatedClient);
      setIsEditing(false);
      setShowReplanPrompt(true);
    } else { alert("Failed to save intel."); }
  };
  const handleReplan = () => { onReplan(); setShowReplanPrompt(false); };
  return (
    <InfoCard title="Client Intel" onEdit={!isEditing ? () => setIsEditing(true) : undefined}>
      <div className="pt-2">
        {isEditing ? (
          <div className="space-y-3">
            <p className="text-xs text-brand-text-muted">Enter each piece of intel on a new line.</p>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={5} className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setIsEditing(false); setNotes(client.preferences?.notes?.join('\n') || ''); }} className="px-3 py-1 text-xs font-semibold bg-white/10 rounded-md">Cancel</button>
              <button onClick={handleSave} className="px-3 py-1 text-xs font-semibold bg-primary-action text-brand-dark rounded-md">Save Intel</button>
            </div>
          </div>
        ) : (
          <ul className="space-y-2">
            {(client.preferences?.notes || []).length > 0 ? (
              (client.preferences.notes).map((note: string, index: number) => (<li key={index} className="flex items-start gap-3 text-sm"><Info size={14} className="flex-shrink-0 mt-0.5" />{note}</li>))
            ) : (<p className="text-xs text-brand-text-muted text-center py-2">No intel added. Click the edit icon to add notes.</p>)}
          </ul>
        )}
        {showReplanPrompt && (
          <div className="mt-4 p-3 bg-primary-action/10 rounded-lg text-center space-y-2 border border-primary-action/20">
            <p className="text-sm font-semibold text-brand-accent">Update the Relationship Campaign with this new information?</p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setShowReplanPrompt(false)} className="px-3 py-1 text-xs bg-white/10 rounded-md">No, Thanks</button>
              <button onClick={handleReplan} className="px-3 py-1 text-xs bg-primary-action text-brand-dark rounded-md">Yes, Update</button>
            </div>
          </div>
        )}
      </div>
    </InfoCard>
  );
};

const RelationshipCampaignCard = ({ messages, onReplan, onUpdateMessage }: { messages: ScheduledMessage[], onReplan: () => void, onUpdateMessage: (updatedMessage: ScheduledMessage) => void }) => {
  const [editingMessage, setEditingMessage] = useState<ScheduledMessage | null>(null);
  const getIconForMessage = (content: string) => {
    const lowerContent = content.toLowerCase();
    if (lowerContent.includes('birthday')) return <Gift size={16} className="text-brand-accent" />;
    if (lowerContent.includes('check-in')) return <Star size={16} className="text-brand-accent" />;
    if (lowerContent.includes('holiday')) return <Sparkles size={16} className="text-brand-accent" />;
    return <Calendar size={16} className="text-brand-accent" />;
  };
  return (
    <>
      <EditMessageModal isOpen={!!editingMessage} onClose={() => setEditingMessage(null)} message={editingMessage} onSave={onUpdateMessage} />
      <InfoCard title="Relationship Campaign">
        <button onClick={onReplan} className="absolute top-4 right-4 p-1 text-brand-text-muted hover:text-white opacity-50 hover:opacity-100 transition-opacity" title="Re-plan Campaign">
          <Zap size={14} />
        </button>
        {messages.length > 0 ? (
          <ul className="space-y-1 pt-2">
            {messages.map(msg => (
              <li key={msg.id} onClick={() => setEditingMessage(msg)} className="group flex items-center justify-between hover:bg-white/5 -mx-2 px-2 py-2 rounded-md cursor-pointer transition-all">
                <div className="flex items-start gap-4">
                  <div className="mt-1 flex-shrink-0">{getIconForMessage(msg.content)}</div>
                  <div>
                    <p className="font-semibold text-sm text-brand-text-main">{new Date(msg.scheduled_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}</p>
                    <p className="text-xs text-brand-text-muted break-words whitespace-pre-wrap">{msg.content.split('\n')[0]}</p>
                  </div>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity pr-1"><Edit2 size={14} className="text-brand-text-muted" /></div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-brand-text-muted mb-3">No campaign planned for this client.</p>
            <button onClick={onReplan} className="w-full px-3 py-2 text-sm font-semibold bg-primary-action/20 text-brand-accent hover:bg-primary-action/30 rounded-md">+ Plan Relationship Campaign</button>
          </div>
        )}
      </InfoCard>
    </>
  );
};


// --- Main Dashboard Page Component ---
export default function DashboardPage() {
  const { clients, setClients } = useAppContext();
  const [properties, setProperties] = useState<Property[]>([]);
  const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // --- STATE REFACTOR for live data ---
  const [loading, setLoading] = useState(true);
  const [conversationSummaries, setConversationSummaries] = useState<Conversation[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [currentMessages, setCurrentMessages] = useState<Message[]>([]);
  
  const [isSending, setIsSending] = useState(false);
  const [composerMessage, setComposerMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'messages' | 'intel'>('messages');

  // --- KEY FEATURE: Fetch initial dashboard data from the backend ---
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      try {
        const [summariesRes, clientsRes, propertiesRes] = await Promise.all([
          fetch('http://localhost:8001/conversations/'),
          fetch('http://localhost:8001/clients/'),
          fetch('http://localhost:8001/properties/')
        ]);

        if (!summariesRes.ok) throw new Error('Failed to fetch conversation summaries');
        if (!clientsRes.ok) throw new Error('Failed to fetch clients');
        if (!propertiesRes.ok) throw new Error('Failed to fetch properties');

        const summariesData = await summariesRes.json();
        const clientsData = await clientsRes.json();
        const propertiesData = await propertiesRes.json();

        setConversationSummaries(summariesData);
        setClients(clientsData);
        setProperties(propertiesData);

        // Auto-select first conversation or one from URL param
        const clientIdFromUrl = searchParams.get('clientId');
        if (clientIdFromUrl) {
          setSelectedClientId(clientIdFromUrl);
        } else if (summariesData.length > 0) {
          setSelectedClientId(summariesData[0].client_id);
        }

      } catch (err: any) {
        setError(err.message || "An unknown error occurred");
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, [setClients, searchParams]);

  // --- KEY FEATURE: Fetch full conversation history when a client is selected ---
  useEffect(() => {
    if (!selectedClientId) {
      setCurrentMessages([]);
      setScheduledMessages([]);
      return;
    }
    
    const fetchConversationDetails = async () => {
      try {
        const [historyRes, scheduledRes] = await Promise.all([
            fetch(`http://localhost:8001/conversations/${selectedClientId}`),
            fetch(`http://localhost:8001/clients/${selectedClientId}/scheduled-messages`)
        ]);

        if (!historyRes.ok) throw new Error('Failed to fetch message history');
        const historyData = await historyRes.json();
        
        // Map backend 'direction' to frontend 'sender'
        const formattedMessages = historyData.map((msg: any) => ({
          id: msg.id,
          sender: msg.direction === 'inbound' ? 'client' : 'agent',
          content: msg.content,
          timestamp: msg.created_at
        }));
        setCurrentMessages(formattedMessages);

        if (!scheduledRes.ok) throw new Error("Failed to fetch scheduled messages");
        const scheduledData = await scheduledRes.json();
        setScheduledMessages(scheduledData);
        
      } catch (err: any) {
        console.error(err);
        setError("Could not load conversation details.");
        setCurrentMessages([]);
        setScheduledMessages([]);
      }
    };

    fetchConversationDetails();
    setActiveTab('messages'); // Always switch to messages tab on selection change
  }, [selectedClientId]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [currentMessages, activeTab]);

  // --- KEY INTEGRATION: Send a reply using the live backend endpoint ---
  const handleSendMessage = async () => {
    if (!composerMessage.trim() || !selectedClientId || isSending) return;
    setIsSending(true);
    const content = composerMessage;
    
    // Optimistic UI update for a responsive feel
    const optimisticMessage: Message = {
      id: `agent-${Date.now()}`,
      sender: 'agent',
      content: content,
      timestamp: new Date().toISOString()
    };
    setCurrentMessages(prev => [...prev, optimisticMessage]);
    setComposerMessage('');

    try {
      const res = await fetch(`http://localhost:8001/conversations/${selectedClientId}/send_reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content }),
      });

      if (!res.ok) {
        throw new Error("Failed to send message");
      }
      // On success, we can optionally refetch history to get the real message from the server,
      // but for now, the optimistic update is sufficient.

    } catch (err) {
      console.error(err);
      setComposerMessage(content); // Restore message on failure
      setCurrentMessages(prev => prev.filter(m => m.id !== optimisticMessage.id)); // Remove optimistic message
      alert("Failed to send message.");
    } finally {
      setIsSending(false);
    }
  };
  
  // Handlers for the right-hand context panel (logic is unchanged)
  const handleUpdateClient = (updatedClient: Client) => { setClients(prev => prev.map(c => c.id === updatedClient.id ? updatedClient : c)); };
  const handlePlanCampaign = async (clientId: string) => {
    await fetch(`http://localhost:8001/clients/${clientId}/plan-campaign`, { method: 'POST' });
    const res = await fetch(`http://localhost:8001/clients/${clientId}/scheduled-messages`);
    const data = await res.json();
    setScheduledMessages(data);
  };
  const handleUpdateScheduledMessage = (updatedMessage: ScheduledMessage) => { setScheduledMessages(prev => prev.map(msg => msg.id === updatedMessage.id ? updatedMessage : msg)); };


  // --- Render Logic ---
  if (loading) { return (<div className="flex flex-col justify-center items-center h-screen text-brand-text-muted bg-brand-dark"><Sparkles className="w-10 h-10 text-brand-accent animate-spin mb-4" /><p className="text-xl font-medium">Loading your AI Nudge workspace...</p></div>); }
  if (error) { return (<div className="flex flex-col justify-center items-center h-screen text-red-400 bg-brand-dark"><p className="text-xl mb-4">Error loading dashboard</p><p className="text-sm font-mono bg-white/5 p-4 rounded-lg">{error}</p></div>); }

  const selectedClient = clients.find(c => c.id === selectedClientId);

  return (
    <div className="h-screen w-screen bg-brand-dark text-brand-text-main font-sans flex overflow-hidden">
      {isSidebarOpen && (<div onClick={() => setIsSidebarOpen(false)} className="fixed inset-0 bg-black/50 z-10 md:hidden"></div>)}
      
      {/* Left Sidebar: Navigation & Conversation List */}
      <aside className={clsx( "bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-20", "absolute md:relative inset-y-0 left-0 w-80", isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0" )}>
        <div className="p-4 flex-shrink-0"> <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority /> </div>
        <nav className="px-4 space-y-1.5 flex-shrink-0">
          <Link href="/dashboard" className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold"> <MessageCircleHeart className="w-5 h-5" /> All Conversations </Link>
          <Link href="/nudges" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors"> <Zap className="w-5 h-5" /> AI Nudges </Link>
        </nav>
        <div className="px-4 my-4 relative flex-shrink-0"> <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-text-muted/50" /> <input type="text" placeholder="Search conversations..." className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent" /> </div>
        <div className="flex-grow overflow-y-auto px-4">
          <ul className="space-y-1">
            {conversationSummaries.map(conv => (
              <li key={conv.id} className={clsx("p-3 rounded-lg cursor-pointer transition-colors border border-transparent", selectedClientId === conv.client_id ? "bg-white/10 border-white/20" : "hover:bg-white/5")} onClick={() => {setSelectedClientId(conv.client_id); setIsSidebarOpen(false);}} >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 overflow-hidden">
                    <Avatar name={conv.client_name} className="w-10 h-10 text-sm flex-shrink-0" />
                    <div className="overflow-hidden">
                      <span className="font-semibold text-brand-text-main">{conv.client_name}</span>
                      <p className="text-brand-text-muted text-sm truncate">{conv.last_message}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end flex-shrink-0">
                    <span className="text-xs text-brand-text-muted/70">{new Date(conv.last_message_time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
                    {conv.unread_count > 0 && (<span className="mt-1 bg-brand-accent text-xs text-brand-dark font-bold rounded-full w-5 h-5 flex items-center justify-center"> {conv.unread_count} </span>)}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <div className="p-4 flex-shrink-0 border-t border-white/5"> <Link href="/profile" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors"> <UserIcon className="w-5 h-5" /> Profile </Link> </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {selectedClient ? (
          <>
            <header className="flex items-center justify-between p-4 border-b border-white/10 bg-brand-dark/50 backdrop-blur-sm sticky top-0 z-10">
              <div className="flex items-center gap-4">
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden"> <Menu className="w-6 h-6" /> </button>
                <Avatar name={selectedClient.full_name} className="w-11 h-11 hidden sm:flex" />
                <div>
                  <h2 className="text-xl font-bold text-brand-text-main">{selectedClient.full_name}</h2>
                  <p className="text-sm text-brand-accent">Online</p>
                </div>
              </div>
              <div className="flex items-center gap-2"> <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 hover:text-brand-text-main"><Phone className="w-5 h-5" /></button> <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 hover:text-brand-text-main"><Video className="w-5 h-5" /></button> </div>
            </header>
            
            <div className="flex-shrink-0 border-b border-white/10 lg:hidden">
              <nav className="flex">
                <button onClick={() => setActiveTab('messages')} className={clsx("flex-1 p-3 text-sm font-semibold text-center", activeTab === 'messages' ? 'text-brand-accent border-b-2 border-brand-accent' : 'text-brand-text-muted')}> Messages </button>
                <button onClick={() => setActiveTab('intel')} className={clsx("flex-1 p-3 text-sm font-semibold text-center", activeTab === 'intel' ? 'text-brand-accent border-b-2 border-brand-accent' : 'text-brand-text-muted')}> Intel </button>
              </nav>
            </div>

            <div className="flex-grow overflow-y-auto">
              <div className={clsx("p-6 space-y-6 h-full", activeTab === 'messages' ? 'block' : 'hidden lg:block')}>
                {currentMessages.map(msg => (
                  <div key={msg.id} className={clsx("flex items-end gap-3", msg.sender === 'client' ? 'justify-start' : 'justify-end')}>
                    {msg.sender === 'client' && <Avatar name={selectedClient.full_name} className="w-8 h-8 text-xs" />}
                    <div className={clsx("p-3 px-4 rounded-t-xl max-w-lg", { 'bg-gray-800 text-brand-text-muted rounded-br-xl': msg.sender === 'client', 'bg-primary-action text-brand-dark font-medium rounded-bl-xl': msg.sender === 'agent' })}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <p className="text-right text-xs mt-1 opacity-70">{new Date(msg.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div className={clsx("p-6 space-y-6 h-full", activeTab === 'intel' ? 'block' : 'hidden')}>
                 <InfoCard title="Client Details"> <div className="flex flex-col items-center text-center"> <Avatar name={selectedClient.full_name} className="w-16 h-16 text-2xl mb-3" /> <h3 className="text-lg font-bold text-brand-text-main">{selectedClient.full_name}</h3> <p className="text-sm text-brand-text-muted">{selectedClient?.email}</p> <div className="mt-4 flex flex-wrap justify-center gap-2"> {selectedClient?.tags.map(tag => (<span key={tag} className="bg-brand-accent/20 text-brand-accent text-xs font-semibold px-2.5 py-1 rounded-full">{tag}</span>))} </div> </div> </InfoCard>
                <ClientIntelCard client={selectedClient} onUpdate={handleUpdateClient} onReplan={() => handlePlanCampaign(selectedClient.id)} />
                <RelationshipCampaignCard messages={scheduledMessages} onReplan={() => handlePlanCampaign(selectedClient.id)} onUpdateMessage={handleUpdateScheduledMessage} />
              </div>
            </div>

            {activeTab === 'messages' && (
              <div className="p-4 bg-black/10 border-t border-white/10 flex-shrink-0">
                <div className="relative bg-white/5 border border-white/10 rounded-xl flex items-center">
                  <input type="text" placeholder="Type your message..." className="flex-grow bg-transparent text-brand-text-main placeholder-brand-text-muted/60 focus:outline-none pl-4" value={composerMessage} onChange={(e) => setComposerMessage(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && composerMessage.trim()) handleSendMessage(); }} disabled={isSending} />
                  <button className="p-3 text-brand-text-muted hover:text-brand-accent"><Paperclip className="w-5 h-5" /></button>
                  <button className="bg-primary-action hover:brightness-110 text-brand-dark p-3 rounded-r-xl m-0.5 disabled:opacity-50" onClick={handleSendMessage} disabled={!composerMessage.trim() || isSending}> <Send className="w-5 h-5" /> </button>
                </div>
              </div>
            )}
          </>
        ) : (
        <div className="flex-1 flex flex-col items-center justify-center h-full text-brand-text-muted p-4">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="absolute top-4 left-4 p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden"> <Menu className="w-6 h-6" /> </button>
            <MessageSquare className="w-16 h-16 mb-4" />
            <p className="text-xl font-medium text-center">Select a conversation</p>
            <p className="text-center">Choose from the list to start messaging.</p>
        </div>)}
      </main>

      {/* Right Sidebar: Context */}
      <aside className="bg-white/5 border-l border-white/10 p-6 flex-col gap-6 overflow-y-auto w-96 flex-shrink-0 hidden lg:flex">
        {selectedClient ? (
          <>
            <InfoCard title="Client Details"> <div className="flex flex-col items-center text-center"> <Avatar name={selectedClient.full_name} className="w-16 h-16 text-2xl mb-3" /> <h3 className="text-lg font-bold text-brand-text-main">{selectedClient.full_name}</h3> <p className="text-sm text-brand-text-muted">{selectedClient.email}</p> <div className="mt-4 flex flex-wrap justify-center gap-2"> {selectedClient.tags.map(tag => (<span key={tag} className="bg-brand-accent/20 text-brand-accent text-xs font-semibold px-2.5 py-1 rounded-full">{tag}</span>))} </div> </div> </InfoCard>
            <ClientIntelCard client={selectedClient} onUpdate={handleUpdateClient} onReplan={() => handlePlanCampaign(selectedClient.id)} />
            <RelationshipCampaignCard messages={scheduledMessages} onReplan={() => handlePlanCampaign(selectedClient.id)} onUpdateMessage={handleUpdateScheduledMessage} />
            <InfoCard title="Properties">
              <ul className="space-y-4">
                {properties.slice(0, 3).map(property => (
                  <li key={property.id} className="flex items-center gap-4">
                    <div className="relative w-20 h-16 bg-brand-dark rounded-md overflow-hidden flex-shrink-0"> <Image src={property.image_urls?.[0] || `https://placehold.co/300x200/0B112B/C4C4C4?text=${property.address.split(',')[0]}`} alt={`Image of ${property.address}`} layout="fill" objectFit="cover" /> </div>
                    <div> <h4 className="font-semibold text-brand-text-main truncate">{property.address}</h4> <p className="text-sm text-brand-text-muted">${property.price.toLocaleString()}</p> <p className="text-xs text-brand-accent font-medium">{property.status}</p> </div>
                  </li>
                ))}
              </ul>
            </InfoCard>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center text-brand-text-muted"> <Users className="w-16 h-16 mb-4" /> <p className="text-lg font-medium">No Client Selected</p> <p className="text-sm">Client context will appear here.</p> </div>
        )}
      </aside>
    </div>
  );
}
