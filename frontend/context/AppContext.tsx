// frontend/context/AppContext.tsx
// --- FINAL, ROBUST VERSION: Fixes stale closures and simplifies dependencies ---

'use client';

import { createContext, useContext, useState, ReactNode, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

// --- (Interfaces are unchanged) ---
export interface User { id: string; full_name: string; email?: string; phone_number: string; twilio_phone_number?: string; user_type: 'realtor' | 'therapist' | 'loan_officer' | null; onboarding_complete: boolean; onboarding_state: { phone_verified: boolean; work_style_set: boolean; contacts_imported: boolean; first_nudges_seen: boolean;[key: string]: any; }; timezone?: string; mls_username?: string; mls_password?: string; license_number?: string; specialties?: string[]; faq_auto_responder_enabled: boolean; vertical?: string; tool_provider?: string; super_user?: boolean; }
export interface Client { id: string; user_id: string; full_name: string; email: string | null; phone: string | null; ai_tags: string[]; user_tags: string[]; preferences: { notes?: string[];[key: string]: any; }; last_interaction: string | null; notes?: string; timezone?: string; }
export interface Property { id: string; address: string; price: number; status: string; image_urls: string[]; }
export interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reasons: string[]; }
export interface CampaignBriefing { id: string; user_id: string; campaign_type: string; headline: string; listing_url?: string; key_intel: { [key: string]: any }; original_draft: string; edited_draft?: string; matched_audience: MatchedClient[]; status: string; is_plan: boolean; parent_message_id?: string; }
export interface Message { id: string; client_id: string; content: string; direction: 'inbound' | 'outbound'; status: string; created_at: string; originally_scheduled_at?: string; ai_drafts?: CampaignBriefing[]; source: 'manual' | 'scheduled' | 'faq_auto_response' | 'instant_nudge'; sender_type: 'user' | 'system' | 'ai'; }
export interface Conversation { id: string; client_id: string; client_name: string; client_phone: string; last_message: string; last_message_time: string; unread_count: number; is_online: boolean; has_messages: boolean; last_message_direction?: 'inbound' | 'outbound'; last_message_source?: 'manual' | 'scheduled' | 'faq_auto_response' | 'instant_nudge'; }
export interface ScheduledMessage { id: string; user_id: string; client_id: string; content: string; scheduled_at_utc: string; timezone: string; status: 'pending' | 'sent' | 'failed' | 'cancelled'; celery_task_id: string | null; playbook_touchpoint_id?: string; is_recurring: boolean; }

// --- (AppContextType is unchanged) ---
interface AppContextType {
  loading: boolean;
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  clients: Client[];
  properties: Property[];
  conversations: Conversation[];
  nudges: CampaignBriefing[];
  socket: WebSocket | null;
  logout: () => void;
  api: { get: (endpoint: string) => Promise<any>; post: (endpoint: string, body: any) => Promise<any>; put: (endpoint: string, body: any) => Promise<any>; del: (endpoint: string) => Promise<any>; };
  login: (token: string) => Promise<User | null>;
  loginAndRedirect: (token: string) => Promise<boolean>;
  fetchDashboardData: () => Promise<void>;
  refreshConversations: () => Promise<void>;
  updateClientInList: (updatedClient: Client) => void;
  refetchScheduledMessagesForClient: (clientId: string) => Promise<ScheduledMessage[]>;
  refreshUser: () => Promise<void>;
  forceRefreshAllData: () => Promise<void>;
  refreshNudges: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [nudges, setNudges] = useState<CampaignBriefing[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const tokenRef = useRef<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const router = useRouter();

  const logout = useCallback(() => {
    Cookies.remove('auth_token');
    tokenRef.current = null;
    setUser(null);
    setIsAuthenticated(false);
    setClients([]);
    setProperties([]);
    setConversations([]);
    setNudges([]);
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setSocket(null);
    router.replace('/auth/login');
  }, [router]);

  const api = useMemo(() => {
    // ... (This function is stable and correct, remains unchanged) ...
    const request = async (endpoint: string, method: string, body?: any, retries = 3) => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const url = `${baseUrl}${endpoint}`;
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (tokenRef.current) headers['Authorization'] = `Bearer ${tokenRef.current}`;
      for (let attempt = 1; attempt <= retries; attempt++) {
        try {
          const config: RequestInit = { method, headers, body: body ? JSON.stringify(body) : undefined };
          const response = await fetch(url, config);
          if (!response.ok) {
            if (response.status === 401) { logout(); throw new Error('Authentication failed'); }
            const errorData = await response.json().catch(() => ({ detail: `API Error: ${response.statusText}` }));
            if (response.status >= 500 && attempt < retries) { console.warn(`API attempt ${attempt} failed with ${response.status}, retrying...`); await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); continue; }
            throw new Error(errorData.detail || 'An unknown error occurred');
          }
          const text = await response.text();
          return text ? JSON.parse(text) : {};
        } catch (error) {
          if (attempt === retries) { throw error; }
          if (error instanceof Error && error.message.includes('4')) { throw error; }
          console.warn(`API attempt ${attempt} failed, retrying...`, error);
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
      }
    };
    return {
      get: (endpoint: string) => request(endpoint, 'GET'),
      post: (endpoint: string, body: any) => request(endpoint, 'POST', body),
      put: (endpoint: string, body: any) => request(endpoint, 'PUT', body),
      del: (endpoint: string) => request(endpoint, 'DELETE'),
    };
  }, [logout]);

  // --- (login, refreshUser, loginAndRedirect remain unchanged) ---
  const refreshUser = useCallback(async () => { try { const userData = await api.get('/api/users/me'); setUser(userData); } catch (error) { console.error("Failed to refresh user data:", error); logout(); } }, [api, logout]);
  const login = useCallback(async (newToken: string): Promise<User | null> => { Cookies.set('auth_token', newToken, { expires: 7, path: '/' }); tokenRef.current = newToken; try { const userData: User = await api.get('/api/users/me'); setUser(userData); setIsAuthenticated(true); return userData; } catch (error) { console.error("Authentication failed:", error); logout(); return null; } }, [api, logout]);
  const loginAndRedirect = async (token: string): Promise<boolean> => { const loggedInUser = await login(token); if (loggedInUser) { if (loggedInUser.onboarding_complete) { router.push('/community'); } else { router.push('/onboarding'); } return true; } return false; };

  // --- (Data fetching functions remain unchanged) ---
  const refreshNudges = useCallback(async () => { if (!tokenRef.current) return; try { console.log("Refreshing AI Nudges..."); const nudgesData = await api.get('/api/campaigns'); setNudges(nudgesData); } catch (error) { console.error("Failed to refresh nudges:", error); } }, [api]);
  const refreshConversations = useCallback(async () => { if (!tokenRef.current) return; try { const conversationsData = await api.get('/api/conversations/'); const sortedConversations = conversationsData.sort((a: any, b: any) => new Date(b.last_message_time).getTime() - new Date(a.last_message_time).getTime()); setConversations(prevConversations => JSON.stringify(prevConversations) === JSON.stringify(sortedConversations) ? prevConversations : sortedConversations); } catch (error) { console.error("Failed to refresh conversations:", error); } }, [api]);
  const fetchDashboardData = useCallback(async () => { if (!tokenRef.current) return; try { const results = await Promise.allSettled([api.get('/api/clients'), api.get('/api/properties'), api.get('/api/conversations/'), api.get('/api/campaigns')]); if (results[0].status === 'fulfilled') setClients(results[0].value); if (results[1].status === 'fulfilled') setProperties(results[1].value); if (results[2].status === 'fulfilled') { const sortedConversations = results[2].value.sort((a: any, b: any) => new Date(b.last_message_time).getTime() - new Date(a.last_message_time).getTime()); setConversations(sortedConversations); } if (results[3].status === 'fulfilled') setNudges(results[3].value); results.forEach((result, index) => { if (result.status === 'rejected') console.error(`Failed to fetch endpoint ${index}:`, result.reason); }); } catch (error) { console.error("A critical error occurred while fetching dashboard data:", error); } }, [api]);
  const forceRefreshAllData = useCallback(async () => { if (!tokenRef.current) return; console.log("Force refreshing all data..."); await fetchDashboardData(); }, [fetchDashboardData]);

  // --- FIX #1: Create refs to hold the latest versions of the refresh functions ---
  const refreshConversationsRef = useRef(refreshConversations);
  const refreshNudgesRef = useRef(refreshNudges);
  useEffect(() => {
    refreshConversationsRef.current = refreshConversations;
    refreshNudgesRef.current = refreshNudges;
  }, [refreshConversations, refreshNudges]);


  // --- WebSocket Connection Logic with all fixes applied ---
  useEffect(() => {
    if (!isAuthenticated || socketRef.current) {
      return;
    }

    const wsUrl = (process.env.NEXT_PUBLIC_API_URL || 'ws://localhost:8001').replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/user?token=${tokenRef.current}`);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established for user notifications.");
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        // FIX #2: Call the latest function from the ref to avoid stale closures
        if (data.type === 'NEW_MESSAGE') {
          console.log("New message received signal. Refreshing conversations list.");
          refreshConversationsRef.current();
        }

        if (data.event === 'nudges_updated' || data.type === 'NUDGES_UPDATED') {
          console.log("Nudges update signal received. Re-fetching nudges.");
          refreshNudgesRef.current();
        }
      } catch (error) {
        console.error("Error handling WebSocket message:", error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed.");
      if (socketRef.current === ws) {
        setSocket(null);
        socketRef.current = null;
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (socketRef.current === ws) {
        setSocket(null);
        socketRef.current = null;
      }
    };

    return () => {
      console.log("Cleaning up WebSocket connection.");
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
    };
    // FIX #3: The dependency array is now minimal and stable. This effect only runs on auth changes.
  }, [isAuthenticated]);

  // --- (Remaining hooks and functions are unchanged) ---
  useEffect(() => { const checkUserSession = async () => { setLoading(true); const savedToken = Cookies.get('auth_token'); if (savedToken) { await login(savedToken); } setLoading(false); }; checkUserSession(); }, [login]);
  useEffect(() => { if (isAuthenticated && user) { fetchDashboardData(); } }, [isAuthenticated, user, fetchDashboardData]);
  const updateClientInList = (updatedClient: Client) => { setClients(prevClients => prevClients.map(c => c.id === updatedClient.id ? updatedClient : c)); };
  const refetchScheduledMessagesForClient = useCallback(async (clientId: string): Promise<ScheduledMessage[]> => { try { return await api.get(`/api/scheduled-messages/?client_id=${clientId}`); } catch (error) { console.error(`Failed to fetch scheduled messages for ${clientId}:`, error); return []; } }, [api]);
  const value = useMemo(() => ({ loading, isAuthenticated, user, token: tokenRef.current, clients, properties, conversations, nudges, socket, logout, api, login, loginAndRedirect, fetchDashboardData, refreshConversations, updateClientInList, refetchScheduledMessagesForClient, refreshUser, forceRefreshAllData, refreshNudges }), [loading, isAuthenticated, user, clients, properties, conversations, nudges, socket, logout, api, login, loginAndRedirect, fetchDashboardData, refreshConversations, updateClientInList, refetchScheduledMessagesForClient, refreshUser, forceRefreshAllData, refreshNudges]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) throw new Error('useAppContext must be used within an AppProvider');
  return context;
};