"use client"; // Required for useState, useEffect, and event handlers

import React, { useState, useEffect, FormEvent } from 'react';
import { Zap, Users, Briefcase, Send, MessageCircle, CalendarClock } from 'lucide-react';

// Define interfaces for our data structures
interface Client {
  id: string;
  name: string;
  email?: string;
  notes?: string;
}

interface Property {
  id: string;
  address: string;
  price?: number;
  image_url?: string;
}

interface ScheduledMessage {
  id: string;
  recipient_name: string; // Assuming we want to display name
  message_preview: string;
  send_time: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'; // Fallback for local dev if env var not set

export default function DashboardPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [aiDraft, setAiDraft] = useState<string>("Click 'Simulate Incoming Message' to see an AI draft here.");
  const [composerMessage, setComposerMessage] = useState<string>("");
  const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial data (mocked for now, will connect to backend)
  useEffect(() => {
    // Mock data - replace with API calls
    setClients([
      { id: 'c1', name: 'John Doe', email: 'john@example.com', notes: 'Looking for 3-bed house' },
      { id: 'c2', name: 'Jane Smith', email: 'jane@example.com', notes: 'Interested in condos' },
    ]);
    setProperties([
      { id: 'p1', address: '123 Main St, Anytown', price: 300000, image_url: 'https://via.placeholder.com/150/191C36/FFFFFF?Text=Main+St' },
      { id: 'p2', address: '456 Oak Ave, Anytown', price: 450000, image_url: 'https://via.placeholder.com/150/20D5B3/FFFFFF?Text=Oak+Ave' },
    ]);
    setScheduledMessages([
        {id: 'sm1', recipient_name: 'Prospective Buyer A', message_preview: 'Following up on 123 Main St...', send_time: 'Tomorrow 10:00 AM'},
        {id: 'sm2', recipient_name: 'Seller B', message_preview: 'Just checking in about the open house...', send_time: 'Next Friday 2:00 PM'}
    ]);

    // Example of fetching actual data (you'll need to create these backend endpoints)
    // fetchClients();
    // fetchProperties();
    // fetchScheduledMessages();
  }, []);

  const handleSimulateIncoming = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // const response = await fetch(`${API_BASE_URL}/inbox/simulate-incoming-message/`, { // Corrected URL
      // For MVP, we use the mock function directly as backend may not be fully up
      // This should be an actual API call
      const response = await fetch(`${API_BASE_URL}/inbox/simulate-incoming-message/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender: "Simulated Client", message_text: "Hi, I saw your listing on Zillow for the property on Elm Street. Can you tell me more?" })
      });
      if (!response.ok) throw new Error(`Error fetching AI draft: ${response.statusText}`);
      const data = await response.json();
      setAiDraft(data.ai_draft_response || "No draft generated.");
    } catch (err) {
      const error = err as Error;
      setError(error.message);
      setAiDraft("Failed to load AI draft.");
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSendNow = async (e: FormEvent) => {
    e.preventDefault();
    if (!composerMessage.trim()) {
      alert("Please type a message.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/campaigns/messages/send-now/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: composerMessage, recipient_id: "client_placeholder_id" }), // Replace with actual recipient
      });
      if (!response.ok) throw new Error(`Error sending message: ${response.statusText}`);
      const data = await response.json();
      alert(data.message || "Message sent status unknown.");
      setComposerMessage(""); // Clear composer
    } catch (err) {
      const error = err as Error;
      setError(error.message);
      alert(`Failed to send message: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAiAssist = async () => {
    if (!composerMessage.trim()) {
      alert("Please type a message to get assistance.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/inbox/receive-message/`, { // This is the "Sparkles" button endpoint
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_message: composerMessage, context: "Client is asking about a new listing." }), // Add relevant context
      });
      if (!response.ok) throw new Error(`Error getting AI assistance: ${response.statusText}`);
      const data = await response.json();
      setComposerMessage(data.ai_suggestion || composerMessage); // Update composer with suggestion
      alert("AI suggestion applied!");
    } catch (err) {
      const error = err as Error;
      setError(error.message);
      alert(`Failed to get AI assistance: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="space-y-6">
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">{error}</div>}

      {/* Simulated Incoming Message & AI Draft */}
      <div className="bg-brand-white p-6 rounded-lg shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold text-brand-primary">AI Draft Response</h2>
          <button
            onClick={handleSimulateIncoming}
            disabled={isLoading}
            className="bg-brand-accent hover:bg-opacity-80 text-brand-primary font-semibold py-2 px-4 rounded-lg shadow transition duration-150 ease-in-out disabled:opacity-50"
          >
            {isLoading ? 'Loading...' : 'Simulate Incoming Message'}
          </button>
        </div>
        <div className="bg-gray-50 p-4 rounded-md min-h-[80px] text-gray-700 whitespace-pre-wrap">
          {aiDraft}
        </div>
      </div>

      {/* Message Composer */}
      <div className="bg-brand-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-semibold text-brand-primary mb-4">Message Composer</h2>
        <form onSubmit={handleSendNow} className="space-y-4">
          <textarea
            value={composerMessage}
            onChange={(e) => setComposerMessage(e.target.value)}
            placeholder="Type your message here..."
            className="w-full h-32 p-3 border border-brand-gray rounded-md focus:ring-2 focus:ring-brand-secondary focus:border-transparent outline-none resize-none"
            disabled={isLoading}
          />
          <div className="flex items-center justify-between space-x-3">
            <button
              type="button"
              onClick={handleAiAssist}
              disabled={isLoading}
              className="flex items-center justify-center space-x-2 bg-brand-secondary hover:bg-opacity-80 text-brand-primary font-semibold py-2 px-4 rounded-lg shadow transition duration-150 ease-in-out disabled:opacity-50"
            >
              <Zap size={18} />
              <span>AI Assist (Sparkles)</span>
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center justify-center space-x-2 bg-brand-primary hover:bg-opacity-80 text-brand-white font-semibold py-2 px-6 rounded-lg shadow transition duration-150 ease-in-out disabled:opacity-50"
            >
              <Send size={18} />
              <span>Send Now</span>
            </button>
          </div>
        </form>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Client List */}
        <div className="bg-brand-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-brand-primary mb-3 flex items-center"><Users size={20} className="mr-2 text-brand-secondary"/>Clients</h2>
          <ul className="space-y-2 max-h-60 overflow-y-auto">
            {clients.map(client => (
              <li key={client.id} className="p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors">
                <h3 className="font-medium text-gray-800">{client.name}</h3>
                <p className="text-sm text-gray-600">{client.email}</p>
              </li>
            ))}
          </ul>
        </div>

        {/* Property List */}
        <div className="bg-brand-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-brand-primary mb-3 flex items-center"><Briefcase size={20} className="mr-2 text-brand-secondary"/>Properties</h2>
          <ul className="space-y-3 max-h-60 overflow-y-auto">
            {properties.map(prop => (
              <li key={prop.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors">
                <img src={prop.image_url} alt={prop.address} className="w-16 h-12 object-cover rounded" />
                <div>
                  <h3 className="font-medium text-gray-800">{prop.address}</h3>
                  <p className="text-sm text-brand-secondary">{prop.price ? `$${prop.price.toLocaleString()}` : 'Price not listed'}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
       {/* Scheduled Messages */}
      <div className="bg-brand-white p-6 rounded-lg shadow-lg">
        <h2 className="text-xl font-semibold text-brand-primary mb-3 flex items-center">
          <CalendarClock size={20} className="mr-2 text-brand-secondary"/>Scheduled Messages
        </h2>
        {scheduledMessages.length > 0 ? (
          <ul className="space-y-2 max-h-60 overflow-y-auto">
            {scheduledMessages.map(msg => (
              <li key={msg.id} className="p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-800">To: {msg.recipient_name}</span>
                  <span className="text-xs text-brand-primary bg-brand-accent/30 px-2 py-1 rounded-full">{msg.send_time}</span>
                </div>
                <p className="text-sm text-gray-600 truncate italic">"{msg.message_preview}"</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No messages currently scheduled.</p>
        )}
      </div>
    </div>
  );
}
