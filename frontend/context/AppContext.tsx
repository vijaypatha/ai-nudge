// frontend/context/AppContext.tsx
//Purpose: manages the authentication token, user data, and provides login and logout functions to the rest of the application

'use client';

import { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';

// --- TYPE INTERFACES (includes new Nudges type) ---
export interface User { id: string; full_name: string; email?: string; phone_number: string; user_type: string; }
export interface Client { id: string; user_id: string; full_name: string; email: string | null; ai_tags: string[]; user_tags: string[]; preferences: { notes?: string[]; [key: string]: any; }; last_interaction: string | null; }
export interface Property { id: string; address: string; price: number; status: string; image_urls: string[]; }
export interface Message { id: string; client_id: string; content: string; direction: 'inbound' | 'outbound'; status: string; created_at: string; }
export interface Conversation { id: string; client_id: string; client_name: string; last_message: string; last_message_time: string; unread_count: number; }
export interface ScheduledMessage { id: string; content: string; scheduled_at: string; status: string; }
export interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reason: string; }
export interface CampaignBriefing { id: string; user_id: string; campaign_type: string; headline: string; listing_url?: string; key_intel: { [key: string]: string }; original_draft: string; edited_draft?: string; matched_audience: MatchedClient[]; status: 'new' | 'launched' | 'dismissed'; }

// --- MODIFIED: Expanded context shape with data and fetchers ---
interface AppContextType {
  loading: boolean;
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  api: { get: (endpoint: string) => Promise<any>; post: (endpoint: string, body: any) => Promise<any>; put: (endpoint: string, body: any) => Promise<any>; del: (endpoint: string) => Promise<any>; };
  
  // --- ADDED: State and fetchers for dashboard data ---
  clients: Client[];
  properties: Property[];
  conversations: Conversation[];
  nudges: CampaignBriefing[];
  fetchDashboardData: () => Promise<void>;
  updateClientInList: (updatedClient: Client) => void;
  refetchScheduledMessagesForClient: (clientId: string) => Promise<ScheduledMessage[]>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  // --- ADDED: State for dashboard data ---
  const [clients, setClients] = useState<Client[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [nudges, setNudges] = useState<CampaignBriefing[]>([]);

  const createApiClient = useCallback((authToken: string | null) => {
    const request = async (endpoint: string, method: string, body?: any) => {
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
      const config: RequestInit = { method, headers };
      if (body) config.body = JSON.stringify(body);
      const response = await fetch(`/api${endpoint}`, config);
      if (!response.ok) {
        if (response.status === 401) logout();
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    };
    return {
      get: (endpoint: string) => request(endpoint, 'GET'),
      post: (endpoint: string, body: any) => request(endpoint, 'POST', body),
      put: (endpoint: string, body: any) => request(endpoint, 'PUT', body),
      del: (endpoint: string) => request(endpoint, 'DELETE'),
    };
  }, []);

  const [api, setApi] = useState(() => createApiClient(null));

  const logout = useCallback(() => {
    Cookies.remove('auth_token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  useEffect(() => { setApi(() => createApiClient(token)); }, [token, createApiClient]);

  const login = async (newToken: string) => {
    Cookies.set('auth_token', newToken, { expires: 7, secure: process.env.NODE_ENV === 'production', sameSite: 'strict' });
    setToken(newToken);
    const tempApi = createApiClient(newToken);
    try {
      const userData = await tempApi.get('/users/me');
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      logout();
    }
  };

  // --- ADDED: Central function to fetch all initial dashboard data ---
  const fetchDashboardData = useCallback(async () => {
    if (!isAuthenticated || !api) return;
    setLoading(true);
    try {
      const [clientsData, propertiesData, conversationsData, nudgesData] = await Promise.all([
        api.get('/clients'),
        api.get('/properties'),
        api.get('/conversations'),
        api.get('/nudges'),
      ]);
      setClients(clientsData);
      setProperties(propertiesData);
      setConversations(conversationsData);
      setNudges(nudgesData);
    } catch (error) {
      console.error("Failed to fetch dashboard data", error);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, api]);

  // --- ADDED: Helper functions to manage state from components ---
  const updateClientInList = (updatedClient: Client) => {
    setClients(prev => prev.map(c => c.id === updatedClient.id ? updatedClient : c));
  };

  const refetchScheduledMessagesForClient = async (clientId: string) => {
    if (!api) return [];
    try {
      return await api.get(`/clients/${clientId}/scheduled-messages`);
    } catch (error) {
      console.error("Failed to refetch scheduled messages", error);
      return [];
    }
  };

  useEffect(() => {
    const checkUserSession = async () => {
      const savedToken = Cookies.get('auth_token');
      if (savedToken) {
        await login(savedToken);
      } else {
        setLoading(false);
      }
    };
    checkUserSession();
  }, []);

  const value = { 
    loading, setLoading, 
    isAuthenticated, user, token,
    login, logout, api,
    clients, properties, conversations, nudges,
    fetchDashboardData,
    updateClientInList,
    refetchScheduledMessagesForClient,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) throw new Error('useAppContext must be used within an AppProvider');
  return context;
};