// frontend/app/dashboard/page.tsx

'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import clsx from 'clsx';
import {
  MessageCircleHeart, Zap, CalendarCheck, Users, MessageSquare,
  Paperclip, Phone, Video, Sparkles, Search, Send
} from "lucide-react";

// --- TYPE SCRIPT INTERFACES ---
interface Client { id: string; full_name: string; email: string; phone?: string; tags: string[]; last_interaction?: string; }
interface Property { id: string; address: string; price: number; status: string; image_urls: string[]; }
interface Message { id: string; sender: 'client' | 'agent' | 'ai'; content: string; timestamp: string; is_ai_draft?: boolean; }
interface Conversation { id:string; client_id: string; client_name: string; last_message: string; last_message_time: string; unread_count: number; messages: Message[]; }
interface AiDraftResponse { ai_draft: string; }
interface IncomingMessageResult { client_id: string; incoming_message: string; ai_draft_response: AiDraftResponse; }

// --- MOCK DATA ---
const mockConversations: Conversation[] = [ { id: 'conv-1', client_id: 'd8b675d0-1f95-4222-bae2-86b208d690ab', client_name: 'Elena Rodriguez', last_message: 'That sounds great! I\'ll take a look at the new listings tonight. Thanks!', last_message_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(), unread_count: 2, messages: [ { id: 'msg-1', sender: 'client', content: 'Hi, checking in on the status of the properties we discussed.', timestamp: new Date(Date.now() - 3600000).toISOString() } ] }, { id: 'conv-2', client_id: 'aa581e90-6e16-4aef-be6a-ff6d67a9603c', client_name: 'Marcus Chen', last_message: 'Perfect, the scheduled showing for Saturday works for us.', last_message_time: new Date(Date.now() - 24 * 3600 * 1000).toISOString(), unread_count: 0, messages: [ { id: 'msg-3', sender: 'agent', content: 'I can schedule a showing for 123 Maple St this weekend. Are you free Saturday or Sunday?', timestamp: new Date(Date.now() - 87000000).toISOString() }, { id: 'msg-4', sender: 'client', content: 'Perfect, the scheduled showing for Saturday works for us.', timestamp: new Date(Date.now() - 86400000).toISOString() }, ] }, { id: 'conv-3', client_id: '3186bed3-27d3-4bab-9c5a-8d2acd461656', client_name: 'Sophia Dubois', last_message: 'Can you send over the market analysis we talked about?', last_message_time: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString(), unread_count: 0, messages: [ { id: 'msg-5', sender: 'client', content: 'Can you send over the market analysis we talked about?', timestamp: new Date(Date.now() - 259200000).toISOString() }, ] } ];

// --- REUSABLE UI COMPONENTS ---
const InfoCard = ({ title, children, className }: { title: string, children: React.ReactNode, className?: string }) => ( <div className={clsx("bg-white/5 border border-white/10 rounded-xl", className)}> <h3 className="text-sm font-semibold text-brand-text-muted px-4 pt-4 pb-2">{title}</h3> <div className="p-4 pt-0"> {children} </div> </div> );
const Avatar = ({ name, className }: { name: string, className?: string }) => { const initials = name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase(); return ( <div className={clsx( "flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none", className )}> {initials} </div> ); };

// --- MAIN DASHBOARD PAGE COMPONENT ---
export default function DashboardPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>(mockConversations);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [composerMessage, setComposerMessage] = useState('');
  const [isAiReplying, setIsAiReplying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [clientsRes, propertiesRes] = await Promise.all([
          fetch('http://localhost:8001/clients'),
          fetch('http://localhost:8001/properties')
        ]);

        if (!clientsRes.ok) throw new Error(`Failed to fetch clients: ${clientsRes.statusText}`);
        const clientsData: Client[] = await clientsRes.json();
        setClients(clientsData);

        if (!propertiesRes.ok) throw new Error(`Failed to fetch properties: ${propertiesRes.statusText}`);
        const propertiesData: Property[] = await propertiesRes.json();
        setProperties(propertiesData);

        if (clientsData.length > 0) {
          const targetClientId = clientsData[0].id;
          const incomingMessagePayload = {
            client_id: targetClientId,
            content: "Hi there! I saw the property at 123 Maple St and I'm interested. Can you tell me more?",
          };
          
          const aiDraftRes = await fetch('http://localhost:8001/inbox/receive-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(incomingMessagePayload),
          });

          if (aiDraftRes.ok) {
            const aiDraftData: IncomingMessageResult = await aiDraftRes.json();
            
            setConversations(prevConversations => {
                const updatedConversations = prevConversations.map(conv => {
                    if (conv.client_id === aiDraftData.client_id) {
                        const newAiMessage: Message = {
                            id: `ai-draft-${Date.now()}`,
                            sender: 'ai',
                            content: aiDraftData.ai_draft_response.ai_draft,
                            timestamp: new Date().toISOString(),
                            is_ai_draft: true
                        };
                        return { ...conv, messages: [...conv.messages, newAiMessage] };
                    }
                    return conv;
                });
                
                const conversationToSelect = updatedConversations.find(c => c.client_id === targetClientId);
                setSelectedConversation(conversationToSelect || null);

                return updatedConversations;
            });
          } else {
            console.error("Could not fetch AI draft:", aiDraftRes.statusText);
            setSelectedConversation(conversations[0] || null);
          }
        } else {
            setSelectedConversation(conversations[0] || null);
        }

      } catch (err: any) {
        setError(err.message || "An unknown error occurred");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => { scrollToBottom(); }, [selectedConversation?.messages]);

  const handleSendNow = async (clientId: string, content: string, draftMessageId: string) => {
    if (isSending || !selectedConversation) return;
    setIsSending(true);
    try {
      const response = await fetch('http://localhost:8001/campaigns/messages/send-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId, content: content }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send message');
      }
      const now = new Date().toISOString();
      const newMessages = selectedConversation.messages.map(msg =>
          msg.id === draftMessageId
              ? { ...msg, sender: 'agent' as const, is_ai_draft: false, timestamp: now }
              : msg
      );
      const updatedConversationObject: Conversation = {
          ...selectedConversation,
          messages: newMessages,
          last_message: content,
          last_message_time: now,
      };
      const newConversationsArray = conversations.map(conv =>
          conv.id === updatedConversationObject.id ? updatedConversationObject : conv
      );
      setSelectedConversation(updatedConversationObject);
      setConversations(newConversationsArray);
    } catch (err: any) {
      console.error("Error sending message:", err);
      alert(`Error: ${err.message}`);
    } finally {
      setIsSending(false);
    }
  };
  
  const handleSendMessage = async () => {
    if (!composerMessage.trim() || !selectedConversation || isSending) return;
    setIsSending(true);
    const content = composerMessage;
    setComposerMessage('');
    try {
      const response = await fetch('http://localhost:8001/campaigns/messages/send-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: selectedConversation.client_id, content: content }),
      });
      if (!response.ok) { throw new Error('Failed to send message'); }
      const now = new Date().toISOString();
      const newMessage: Message = { id: `agent-${now}`, sender: 'agent', content: content, timestamp: now, is_ai_draft: false };
      const updatedConv = { ...selectedConversation, messages: [...selectedConversation.messages, newMessage], last_message: content, last_message_time: now };
      setSelectedConversation(updatedConv);
      setConversations(conversations.map(c => c.id === updatedConv.id ? updatedConv : c));
    } catch (err) {
      console.error(err);
      setComposerMessage(content);
      alert("Failed to send message. Please try again.");
    } finally {
      setIsSending(false);
    }
  };

  const handleAiAssistance = async () => {
    if (!composerMessage.trim() || !selectedConversation || isAiReplying) return;
    setIsAiReplying(true);
    const content = composerMessage;
    try {
      const response = await fetch('http://localhost:8001/inbox/receive-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: selectedConversation.client_id, content: content }),
      });
      if (!response.ok) { throw new Error('AI assistant failed to respond.'); }
      const aiDraftData: IncomingMessageResult = await response.json();
      const newAiMessage: Message = { id: `ai-draft-${Date.now()}`, sender: 'ai', content: aiDraftData.ai_draft_response.ai_draft, timestamp: new Date().toISOString(), is_ai_draft: true };
      const updatedConv = { ...selectedConversation, messages: [...selectedConversation.messages, newAiMessage] };
      setSelectedConversation(updatedConv);
      setConversations(conversations.map(c => c.id === updatedConv.id ? updatedConv : c));
      setComposerMessage('');
    } catch (err) {
      console.error(err);
      alert("AI Assistant failed. Please try again.");
    } finally {
      setIsAiReplying(false);
    }
  };

  if (loading) { return ( <div className="flex flex-col justify-center items-center h-screen text-brand-text-muted bg-brand-dark"> <Sparkles className="w-10 h-10 text-brand-accent animate-spin mb-4" /> <p className="text-xl font-medium">Loading your AI Nudge workspace...</p> </div> ); }
  if (error) { return ( <div className="flex flex-col justify-center items-center h-screen text-red-400 bg-brand-dark"> <p className="text-xl mb-4">Error loading dashboard</p> <p className="text-sm font-mono bg-white/5 p-4 rounded-lg">{error}</p> <p className="text-xs text-brand-text-muted mt-4">Please ensure your backend server is running.</p> </div> ); }

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-[320px_1fr] lg:grid-cols-[320px_1fr_340px] bg-brand-dark text-brand-text-main font-sans">
      <aside className="bg-white/5 border-r border-white/10 p-4 flex flex-col gap-6">
        <div className="flex items-center h-8">
            <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={140} height={32} priority />
        </div>
        <nav className="space-y-1.5">
          <a href="#" className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold">
            <MessageCircleHeart className="w-5 h-5" /> All Conversations
          </a>
          <a href="#" className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors">
            <Zap className="w-5 h-5" /> AI Nudges
          </a>
        </nav>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-text-muted/50" />
          <input type="text" placeholder="Search conversations..." className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent" />
        </div>
        <div className="flex flex-col flex-grow -mr-2 overflow-y-auto">
          <ul className="pr-2 space-y-1">
            {conversations.map(conv => (
              <li key={conv.id} className={clsx( "p-3 rounded-lg cursor-pointer transition-colors border border-transparent", selectedConversation?.id === conv.id ? "bg-white/10 border-white/20" : "hover:bg-white/5" )} onClick={() => setSelectedConversation(conv)} >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                     <Avatar name={conv.client_name} className="w-10 h-10 text-sm flex-shrink-0" />
                     <div>
                        <span className="font-semibold text-brand-text-main">{conv.client_name}</span>
                        <p className="text-brand-text-muted text-sm truncate max-w-[150px]">{conv.last_message}</p>
                     </div>
                  </div>
                  <div className="flex flex-col items-end flex-shrink-0">
                    <span className="text-xs text-brand-text-muted/70">{new Date(conv.last_message_time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
                    {conv.unread_count > 0 && ( <span className="mt-1 bg-brand-accent text-xs text-brand-dark font-bold rounded-full w-5 h-5 flex items-center justify-center"> {conv.unread_count} </span> )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </aside>
      <main className="bg-brand-dark flex flex-col">
        {selectedConversation ? (
          <>
            <header className="flex items-center justify-between p-4 border-b border-white/10 bg-brand-dark/50 backdrop-blur-sm">
              <div className="flex items-center gap-4">
                <Avatar name={selectedConversation.client_name} className="w-11 h-11" />
                <div>
                  <h2 className="text-xl font-bold text-brand-text-main">{selectedConversation.client_name}</h2>
                  <p className="text-sm text-brand-accent">Online</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 hover:text-brand-text-main"><Phone className="w-5 h-5"/></button>
                <button className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 hover:text-brand-text-main"><Video className="w-5 h-5"/></button>
              </div>
            </header>
            <div className="flex-grow overflow-y-auto p-6 space-y-6">
              {selectedConversation.messages.map(msg => (
                <div key={msg.id} className={clsx("flex items-end gap-3", msg.sender === 'client' ? 'justify-start' : 'justify-end')}>
                  {msg.is_ai_draft ? ( <div className="w-full max-w-xl p-4 rounded-xl bg-gradient-to-br from-gray-700/50 to-gray-800/50 border border-brand-accent/50 shadow-lg"> <div className="flex items-start gap-3"> <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-brand-accent/20"> <Sparkles className="w-5 h-5 text-brand-accent" /> </div> <div> <p className="text-sm font-semibold text-brand-accent mb-1">AI Generated Draft</p> <p className="text-brand-text-main">{msg.content}</p> </div> </div> <div className="flex justify-end gap-2 mt-4"> <button className="px-4 py-1.5 text-sm font-semibold text-brand-text-main bg-white/10 hover:bg-white/20 rounded-md">Edit</button> <button className="px-4 py-1.5 text-sm font-semibold text-brand-dark bg-primary-action hover:brightness-110 rounded-md flex items-center gap-2 disabled:opacity-50" onClick={() => handleSendNow(selectedConversation.client_id, msg.content, msg.id)} disabled={isSending}> {isSending ? 'Sending...' : 'Send'} <Send className="w-4 h-4" /> </button> </div> </div> ) : ( <> {msg.sender === 'client' && <Avatar name={selectedConversation.client_name} className="w-8 h-8 text-xs" />} <div className={clsx("p-3 px-4 rounded-t-xl max-w-lg", { 'bg-gray-800 text-brand-text-muted rounded-br-xl': msg.sender === 'client', 'bg-primary-action text-brand-dark font-medium rounded-bl-xl': msg.sender === 'agent' })}> <p>{msg.content}</p> <p className="text-right text-xs mt-1 opacity-70"> {new Date(msg.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} </p> </div> </> )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="p-4 bg-black/10 border-t border-white/10">
                <div className="relative bg-white/5 border border-white/10 rounded-xl flex items-center">
                    <button className="p-3 text-brand-text-muted hover:text-brand-accent disabled:opacity-50 disabled:cursor-not-allowed" onClick={handleAiAssistance} disabled={!composerMessage.trim() || isAiReplying} title="Get AI Assistance" >
                      {isAiReplying ? <Sparkles className="w-5 h-5 animate-spin"/> : <Sparkles className="w-5 h-5"/>}
                    </button>
                    <input type="text" placeholder="Type your message, or ask AI..." className="flex-grow bg-transparent text-brand-text-main placeholder-brand-text-muted/60 focus:outline-none" value={composerMessage} onChange={(e) => setComposerMessage(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }} disabled={isAiReplying || isSending} />
                    <button className="p-3 text-brand-text-muted hover:text-brand-accent"><Paperclip className="w-5 h-5"/></button>
                    <button className="bg-primary-action hover:brightness-110 text-brand-dark p-3 rounded-r-xl m-0.5 disabled:opacity-50" onClick={handleSendMessage} disabled={!composerMessage.trim() || isSending || isAiReplying} >
                      <Send className="w-5 h-5" /> 
                    </button>
                </div>
            </div>
          </>
        ) : ( <div className="flex flex-col items-center justify-center h-full text-brand-text-muted"> <MessageSquare className="w-16 h-16 mb-4" /> <p className="text-xl font-medium">Select a conversation</p> <p>Choose from the list to start messaging.</p> </div> )}
      </main>
      <aside className="bg-white/5 border-l border-white/10 p-6 flex-col gap-6 overflow-y-auto hidden lg:flex">
        {selectedConversation ? (
          <>
            <InfoCard title="Client Details" className="bg-transparent border-none">
              <div className="flex flex-col items-center text-center">
                <Avatar name={selectedConversation.client_name} className="w-16 h-16 text-2xl mb-3"/>
                <h3 className="text-lg font-bold text-brand-text-main">{selectedConversation.client_name}</h3>
                <p className="text-sm text-brand-text-muted">{clients.find(c => c.id === selectedConversation.client_id)?.email}</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {clients.find(c => c.id === selectedConversation.client_id)?.tags.map(tag => ( <span key={tag} className="bg-brand-accent/20 text-brand-accent text-xs font-semibold px-2.5 py-1 rounded-full"> {tag} </span> ))}
                </div>
              </div>
            </InfoCard>
            <InfoCard title="Quick Nudges">
              <div className="space-y-2">
                <button className="w-full py-2 px-4 rounded-md bg-white/5 hover:bg-white/10 text-brand-text-muted font-semibold">Send Market Update</button>
                <button className="w-full py-2 px-4 rounded-md bg-white/5 hover:bg-white/10 text-brand-text-muted font-semibold">Schedule Showing</button>
              </div>
            </InfoCard>
            <InfoCard title="Properties">
               <ul className="space-y-4">
                  {properties.slice(0, 3).map(property => ( 
                    <li key={property.id} className="flex items-center gap-4">
                      <div className="relative w-20 h-16 bg-brand-dark rounded-md overflow-hidden flex-shrink-0">
                         <Image src={property.image_urls?.[0] || `https://placehold.co/300x200/0B112B/C4C4C4?text=${property.address.split(',')[0]}`} alt={`Image of ${property.address}`} layout="fill" objectFit="cover" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-brand-text-main truncate">{property.address}</h4>
                        <p className="text-sm text-brand-text-muted">${property.price.toLocaleString()}</p>
                        <p className="text-xs text-brand-accent font-medium">{property.status}</p>
                      </div>
                    </li>
                  ))}
               </ul>
            </InfoCard>
          </>
        ) : ( <div className="flex flex-col items-center justify-center h-full text-center text-brand-text-muted"> <Users className="w-16 h-16 mb-4"/> <p className="text-lg font-medium">No Client Selected</p> <p className="text-sm">Client context will appear here.</p> </div> )}
      </aside>
    </div>
  );
}