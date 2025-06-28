// File Path: frontend/app/nudges/page.tsx
// This is the complete, unabbreviated, and corrected code for this file.
// Purpose: This page fetches all actionable nudges and uses frontend logic to display them correctly:
// High-confidence nudges appear as individual, detailed cards, while all low-confidence insights
// are grouped into a single, expandable card.

'use client'; // This directive indicates that this component should be rendered on the client-side.

// --- Imports ---
import { useState, useEffect } from 'react'; // React hooks for managing component state and side effects.
import Image from 'next/image'; // Next.js component for optimized image handling.
import Link from 'next/link'; // Next.js component for client-side navigation.
import { useAppContext } from '../../context/AppContext'; // Custom hook to access application-wide context (e.g., clients data).
import type { Client } from '../../context/AppContext'; // Type definition for the Client data from the AppContext.
import clsx from 'clsx'; // Utility for conditionally joining CSS class names together.
import {
  MessageCircleHeart,
  Zap,
  User as UserIcon,
  Sparkles,
  Menu,
  BrainCircuit,
  Bot,
  Send,
  Edit2,
  Check,
  X,
  RefreshCw,
  PlusCircle,
  Lightbulb,
  ChevronDown,
} from 'lucide-react'; // Importing various icons from the 'lucide-react' library.

// --- Type Definitions ---
/**
 * Interface for a client that has been matched to a campaign briefing.
 */
interface MatchedClient {
  client_id: string;
  client_name: string;
  match_score: number;
  match_reason: string;
}

/**
 * Interface for a campaign briefing, representing an AI-generated nudge or insight.
 * 'status' determines how the briefing is displayed on the page.
 */
interface CampaignBriefing {
  id: string;
  headline: string;
  original_draft: string;
  matched_audience: MatchedClient[];
  status: 'new' | 'insight' | 'approved' | 'dismissed'; // 'new' for high-confidence, 'insight' for low-confidence.
  key_intel: { [key: string]: string | number }; // Key metrics or insights related to the briefing.
  edited_draft: string | null; // Stores a user-edited version of the message draft, if any.
}

// --- Reusable Components ---

/**
 * Avatar component: Displays a client's initials within a circular avatar.
 * @param {string} name - The full name of the client.
 * @param {string} [className] - Optional additional CSS classes for styling.
 */
const Avatar = ({ name, className }: { name: string; className?: string }) => {
  // Extracts the first two initials from the name and converts them to uppercase.
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

/**
 * AiSuggestionCard component: Renders a single, detailed card for high-confidence AI nudges.
 * These nudges are actionable and directly suggest a message and audience.
 * @param {CampaignBriefing} briefing - The campaign briefing data for this card.
 * @param {(updatedBriefing: CampaignBriefing) => void} onUpdate - Callback to update the parent's state
 * after a briefing is approved or dismissed.
 */
const AiSuggestionCard = ({
  briefing,
  onUpdate,
}: {
  briefing: CampaignBriefing;
  onUpdate: (updatedBriefing: CampaignBriefing) => void;
}) => {
  // State to control the visibility of the message composer area.
  const [isComposerVisible, setIsComposerVisible] = useState(false);
  // State for the message draft, initialized with the original AI-generated draft.
  const [draft, setDraft] = useState(briefing.original_draft);
  // State to manage the loading/submitting status during API calls.
  const [isSubmitting, setIsSubmitting] = useState(false);
  // State to control the expansion of the audience list.
  const [isAudienceExpanded, setIsAudienceExpanded] = useState(false);

  // Extract the first client for primary display and the rest for the expandable list.
  const topClient = briefing.matched_audience[0];
  const otherClients = briefing.matched_audience.slice(1);

  /**
   * Handles updating the campaign briefing status (e.g., 'approved' or 'dismissed') via API.
   * @param {'approved' | 'dismissed'} status - The new status to set for the briefing.
   */
  const handleUpdate = async (status: 'approved' | 'dismissed') => {
    setIsSubmitting(true); // Indicate that a submission is in progress.
    try {
      // Make a PUT request to update the campaign on the backend.
      const res = await fetch(`http://localhost:8001/campaigns/${briefing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited_draft: draft, status: status }), // Send the current draft and new status.
      });

      if (!res.ok) {
        // Throw an error if the response is not successful (e.g., 4xx, 5xx).
        throw new Error(`Failed to update campaign: ${res.statusText}`);
      }

      const updatedData = await res.json(); // Parse the JSON response containing the updated briefing.
      onUpdate(updatedData); // Call the parent's onUpdate callback to refresh the main list.
    } catch (error) {
      console.error('Error updating campaign:', error); // Log any errors encountered during the process.
    } finally {
      setIsSubmitting(false); // Reset submitting state regardless of success or failure.
    }
  };

  return (
    <div
      className={clsx(
        'bg-white/5 border border-white/10 rounded-xl overflow-hidden transition-opacity duration-500',
        briefing.status !== 'new' ? 'opacity-40' : '' // Grey out the card if it's no longer 'new'.
      )}
    >
      {/* Card Header: Displays the nudge headline with an icon. */}
      <header className="p-4 bg-black/10">
        <h3 className="font-bold text-lg text-brand-text-main flex items-center gap-3">
          <Sparkles size={18} className="text-green-400" /> {briefing.headline}
        </h3>
      </header>

      {/* Card Body: Contains key intelligence and audience details. */}
      <div className="p-4">
        {/* Key Intelligence Metrics */}
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

        {/* Suggested Audience Section */}
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-semibold text-brand-text-main">Suggested Audience</h4>
          <button className="flex items-center gap-1.5 text-sm text-brand-accent hover:text-white">
            <PlusCircle size={14} />Manage Audience ({briefing.matched_audience.length})
          </button>
        </div>

        {/* Audience List Display (top client always visible, others expandable) */}
        <div className="space-y-2">
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
              // Render all other matched clients if the list is expanded.
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
              // Button to expand the list of other clients if not expanded.
              <button
                onClick={() => setIsAudienceExpanded(true)}
                className="w-full text-left p-2 text-sm text-brand-text-muted hover:bg-black/40 rounded-md"
              >
                + {otherClients.length} other high-fit client(s)
              </button>
            ))}
        </div>
      </div>

      {/* Card Footer: Message composer or "View & Send" button. */}
      <div className="p-4 border-t border-white/10 bg-black/10">
        {isComposerVisible ? (
          // Message composer section (visible when expanded).
          <div className="space-y-4">
            <h4 className="font-semibold text-brand-text-main">Edit Message Draft</h4>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="w-full h-32 bg-black/20 border border-white/20 rounded-lg p-3 text-sm"
              disabled={isSubmitting} // Disable textarea while submitting.
            />
            <div className="flex items-center gap-2">
              {/* Send button: Approves the briefing and sends the message. */}
              <button
                onClick={() => handleUpdate('approved')}
                disabled={isSubmitting || briefing.status !== 'new'} // Disable if submitting or already acted upon.
                className="flex-1 flex items-center justify-center gap-2 p-2.5 bg-primary-action text-brand-dark font-semibold rounded-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? <RefreshCw size={18} className="animate-spin" /> : <Send size={18} />}Send
              </button>
              {/* Dismiss button: Dismisses the briefing. */}
              <button
                onClick={() => handleUpdate('dismissed')}
                disabled={isSubmitting || briefing.status !== 'new'} // Disable if submitting or already acted upon.
                className="p-2.5 bg-white/10 rounded-md hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Dismiss"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        ) : (
          // Initial view with prompt and "View & Send" button.
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

/**
 * AiInsightCard component: Renders a single low-confidence "Insight" briefing.
 * These are shown within the `InsightGroupCard` as they don't have a direct audience match.
 * @param {CampaignBriefing} briefing - The campaign briefing data for this insight.
 */
const AiInsightCard = ({ briefing }: { briefing: CampaignBriefing }) => {
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
        <button className="p-2.5 bg-primary-action text-brand-dark rounded-md text-sm font-semibold">
          Build Audience
        </button>
      </div>
    </div>
  );
};

/**
 * InsightGroupCard component: Renders a collapsible group card that contains all low-confidence insights.
 * @param {CampaignBriefing[]} insights - An array of low-confidence campaign briefings (insights).
 */
const InsightGroupCard = ({ insights }: { insights: CampaignBriefing[] }) => {
  // State to control the expanded/collapsed state of the insights group.
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white/5 border-2 border-dashed border-white/10 rounded-xl overflow-hidden">
      {/* Header of the insights group, which is clickable to toggle expansion. */}
      <header
        className="p-4 flex justify-between items-center cursor-pointer hover:bg-white/5"
        onClick={() => setIsExpanded(!isExpanded)} // Toggles the `isExpanded` state.
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
        {/* Chevron icon rotates based on expanded state. */}
        <ChevronDown size={20} className={clsx('transition-transform', isExpanded && 'rotate-180')} />
      </header>

      {/* Conditional rendering: displays individual AiInsightCard components only when expanded. */}
      {isExpanded && (
        <div className="p-4 border-t border-white/10 space-y-4">
          {insights.map((briefing) => (
            <AiInsightCard key={briefing.id} briefing={briefing} />
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * InstantNudgeCreator component: Provides an interface for users to manually create and send nudges.
 * This includes an audience builder and message drafting area.
 */
const InstantNudgeCreator = () => {
  const { clients } = useAppContext(); // Access the global list of clients from the AppContext.
  const [filteredClients, setFilteredClients] = useState<Client[]>([]); // State for clients displayed in the audience filter.
  const [selectedClients, setSelectedClients] = useState<Set<string>>(new Set()); // State for the set of currently selected client IDs.

  // Effect hook to initialize `filteredClients` when `clients` from context become available or change.
  useEffect(() => {
    setFilteredClients(clients);
  }, [clients]); // Dependency array ensures this runs only when 'clients' changes.

  /**
   * Handles the "Select All Filtered" checkbox.
   * @param {React.ChangeEvent<HTMLInputElement>} e - The change event from the checkbox.
   */
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedClients(new Set(filteredClients.map((c) => c.id))); // Select all currently filtered clients.
    } else {
      setSelectedClients(new Set()); // Deselect all clients.
    }
  };

  /**
   * Handles the selection/deselection of an individual client.
   * @param {string} clientId - The ID of the client to toggle.
   */
  const handleSelectClient = (clientId: string) => {
    const newSelection = new Set(selectedClients); // Create a mutable copy of the current selection.
    if (newSelection.has(clientId)) {
      newSelection.delete(clientId); // If client is already selected, deselect it.
    } else {
      newSelection.add(clientId); // If client is not selected, select it.
    }
    setSelectedClients(newSelection); // Update the state with the new selection.
  };

  return (
    <div className="space-y-8">
      {/* Section 1: Target Your Audience */}
      <section>
        <div className="flex items-center gap-3 mb-4">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">
            1
          </span>
          <h2 className="text-2xl font-bold">Target Your Audience</h2>
        </div>
        <div className="p-6 bg-white/5 rounded-xl border border-white/10">
          {/* Natural Language Audience Builder input */}
          <label className="text-sm font-semibold text-brand-text-muted" htmlFor="audience-builder">
            Natural Language Audience Builder ✨
          </label>
          <input
            id="audience-builder"
            type="text"
            placeholder="e.g., “investors I haven't talked to in six months”"
            className="w-full mt-2 bg-black/20 border border-white/20 rounded-lg p-3 text-brand-text-main focus:outline-none focus:ring-2 focus:ring-brand-accent"
          />
          <div className="my-4 text-center text-sm text-brand-text-muted">or use traditional filters</div>

          {/* Traditional Filters: Client list with checkboxes */}
          <div className="border border-white/10 rounded-lg max-h-64 overflow-y-auto">
            <div className="p-3 border-b border-white/10 sticky top-0 bg-brand-dark/50 backdrop-blur-sm">
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent"
                  checked={selectedClients.size > 0 && selectedClients.size === filteredClients.length}
                  onChange={handleSelectAll}
                />
                Select All Filtered ({selectedClients.size}/{filteredClients.length})
              </label>
            </div>
            {filteredClients.map((client) => (
              <div key={client.id} className="border-b border-white/10 last:border-b-0">
                <label className="flex items-center gap-3 p-3 hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent"
                    checked={selectedClients.has(client.id)}
                    onChange={() => handleSelectClient(client.id)}
                  />
                  <Avatar name={client.full_name} className="w-8 h-8 text-xs" />
                  {client.full_name}
                </label>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 2: Draft and Send Nudge */}
      <section>
        <div className="flex items-center gap-3 mb-4">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-accent text-brand-dark font-bold">
            2
          </span>
          <h2 className="text-2xl font-bold">Draft and Send Nudge</h2>
        </div>
        <div className="p-6 bg-white/5 rounded-xl border border-white/10 space-y-4">
          {/* Topic/Goal input for AI drafting */}
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
          {/* Message textarea */}
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
          {/* Action buttons: Draft with AI and Send. */}
          <div className="flex flex-wrap items-center gap-4">
            <button className="flex items-center gap-2 p-3 bg-white/10 rounded-md font-semibold hover:bg-white/20">
              <Bot size={18} /> Draft with AI
            </button>
            <button className="flex items-center gap-2 p-3 bg-primary-action text-brand-dark rounded-md font-semibold hover:brightness-110">
              <Send size={18} /> Send to {selectedClients.size} recipients
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

/**
 * NudgesPage component: The main entry point for the AI Nudges page.
 * Manages fetching briefings, sidebar state, active tab, and renders the appropriate content.
 */
export default function NudgesPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // State to control the visibility of the sidebar on mobile.
  const [activeTab, setActiveTab] = useState<'ai_suggestions' | 'instant_nudge'>('ai_suggestions'); // State to control which main tab is active.
  const [briefings, setBriefings] = useState<CampaignBriefing[]>([]); // State to store all fetched campaign briefings.
  const [loading, setLoading] = useState(true); // State to indicate data loading status.

  /**
   * Fetches all campaign briefings from the backend API.
   * This function updates the `briefings` state with the fetched data.
   */
  const fetchBriefings = async () => {
    setLoading(true); // Set loading to true before starting the fetch.
    try {
      const res = await fetch('http://localhost:8001/nudges/'); // API call to the nudges endpoint.
      if (!res.ok) {
        // Handle non-successful HTTP responses.
        throw new Error(`Failed to fetch nudges: ${res.statusText}`);
      }
      const data: CampaignBriefing[] = await res.json(); // Parse the JSON response into CampaignBriefing array.
      setBriefings(data); // Update the state with the fetched briefings.
    } catch (err) {
      console.error('Error fetching nudges:', err); // Log any errors during the fetch operation.
    } finally {
      setLoading(false); // Set loading to false regardless of success or failure.
    }
  };

  // useEffect hook to trigger `fetchBriefings` when the component mounts.
  useEffect(() => {
    fetchBriefings();
  }, []); // Empty dependency array ensures this effect runs only once after the initial render.

  /**
   * Callback function passed to `AiSuggestionCard` to update a specific briefing in the state.
   * This ensures the main list reflects changes (e.g., status updates) without refetching all data.
   * @param {CampaignBriefing} updatedBriefing - The briefing object with updated data.
   */
  const handleCampaignUpdate = (updatedBriefing: CampaignBriefing) => {
    setBriefings((prevBriefings) =>
      prevBriefings.map((b) => (b.id === updatedBriefing.id ? updatedBriefing : b))
    );
  };

  // Logic to separate high-confidence ('new') nudges from low-confidence ('insight') nudges.
  // This enables distinct rendering logic for each type.
  const highConfidenceNudges = briefings.filter((b) => b.status === 'new');
  const lowConfidenceInsights = briefings.filter((b) => b.status === 'insight');

  return (
    <div className="min-h-screen flex bg-brand-dark text-brand-text-main font-sans">
      {/* Mobile Sidebar Overlay: Appears when sidebar is open on small screens. */}
      {isSidebarOpen && (
        <div onClick={() => setIsSidebarOpen(false)} className="fixed inset-0 bg-black/50 z-10 md:hidden"></div>
      )}

      {/* Sidebar Navigation */}
      <aside
        className={clsx(
          'bg-brand-dark border-r border-white/10 flex flex-col transition-transform duration-300 ease-in-out z-20',
          'absolute md:relative inset-y-0 left-0 w-80', // Absolute positioning for mobile, relative for desktop.
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0' // Controls sidebar slide animation.
        )}
      >
        <div className="p-4 flex-shrink-0">
          <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={260} height={60} priority />
        </div>
        <nav className="px-4 space-y-1.5 flex-grow">
          {/* Link to All Conversations dashboard. */}
          <Link
            href="/dashboard"
            className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors"
          >
            <MessageCircleHeart className="w-5 h-5" /> All Conversations
          </Link>
          {/* Link to AI Nudges page (currently active). */}
          <Link
            href="/nudges"
            className="flex items-center gap-3 p-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-semibold"
          >
            <Zap className="w-5 h-5" /> AI Nudges
          </Link>
        </nav>
        <div className="p-4 flex-shrink-0 border-t border-white/5">
          {/* Link to Profile page. */}
          <Link
            href="/profile"
            className="flex items-center gap-3 p-2.5 rounded-lg text-brand-text-muted hover:bg-white/5 transition-colors"
          >
            <UserIcon className="w-5 h-5" /> Profile
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 sm:p-10 overflow-y-auto">
        {/* Page Header: Title and tab navigation. */}
        <header className="flex items-start sm:items-center justify-between gap-4 mb-8 flex-col sm:flex-row">
          <div className="flex items-center gap-4">
            {/* Mobile menu button to toggle sidebar. */}
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-full text-brand-text-muted hover:bg-white/10 md:hidden"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-3xl font-bold">AI Nudges</h1>
          </div>
          {/* Tab buttons for "AI Suggestions" and "Instant Nudge". */}
          <div className="bg-black/20 p-1 rounded-lg flex items-center gap-1 self-stretch sm:self-auto">
            <button
              onClick={() => setActiveTab('ai_suggestions')}
              className={clsx(
                'px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none',
                { 'bg-white/10': activeTab === 'ai_suggestions' } // Apply highlighted style if active.
              )}
            >
              AI Suggestions
            </button>
            <button
              onClick={() => setActiveTab('instant_nudge')}
              className={clsx(
                'px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none',
                { 'bg-white/10': activeTab === 'instant_nudge' } // Apply highlighted style if active.
              )}
            >
              Instant Nudge
            </button>
          </div>
        </header>

        {/* Content based on active tab */}
        <div>
          {activeTab === 'ai_suggestions' && (
            <div className="space-y-6">
              {loading && <p>Loading suggestions...</p>}
              {/* Message displayed when no briefings are found after loading. */}
              {!loading && briefings.length === 0 && (
                <div className="text-center py-16 border-2 border-dashed border-white/10 rounded-xl">
                  <BrainCircuit className="mx-auto h-12 w-12 text-brand-text-muted" />
                  <h3 className="mt-2 text-lg font-medium">No AI Suggestions Yet</h3>
                  <p className="mt-1 text-sm text-brand-text-muted">
                    The AI is watching the market. New opportunities will appear here.
                  </p>
                </div>
              )}
              {/* Render high-confidence nudges as individual detailed cards. */}
              {highConfidenceNudges.map((briefing) => (
                <AiSuggestionCard key={briefing.id} briefing={briefing} onUpdate={handleCampaignUpdate} />
              ))}
              {/* Render the single grouped card for low-confidence insights if any exist. */}
              {lowConfidenceInsights.length > 0 && <InsightGroupCard insights={lowConfidenceInsights} />}
            </div>
          )}
          {/* Render the InstantNudgeCreator component if the "Instant Nudge" tab is active. */}
          {activeTab === 'instant_nudge' && <InstantNudgeCreator />}
        </div>
      </main>
    </div>
  );
}