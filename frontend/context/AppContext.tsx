// frontend/context/AppContext.tsx
// DEFINITIVE FIX: Centralizes post-login redirect logic to fix the new user
// onboarding flow by inspecting the user's `onboarding_complete` status.

'use client';

import { createContext, useContext, useState, ReactNode, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

// --- Type Definitions ---

// MODIFIED: Added onboarding_complete and onboarding_state to the User interface
export interface User {
  id: string;
  full_name: string;
  email?: string;
  phone_number: string;
  user_type: string | null; // Can be null before onboarding
  onboarding_complete: boolean;
  onboarding_state: {
      phone_verified: boolean;
      work_style_set: boolean;
      contacts_imported: boolean;
      first_nudges_seen: boolean;
      [key: string]: any;
  };
}

export interface Client { id: string; user_id: string; full_name: string; email: string | null; ai_tags: string[]; user_tags: string[]; preferences: { notes?: string[]; [key: string]: any; }; last_interaction: string | null; }
export interface Property { id: string; address: string; price: number; status: string; image_urls: string[]; }
export interface Message { id:string; client_id: string; content: string; direction: 'inbound' | 'outbound'; status: string; created_at: string; }
export interface Conversation { id: string; client_id: string; client_name: string; last_message: string; last_message_time: string; unread_count: number; }
export interface ScheduledMessage { id: string; user_id: string; client_id: string; content: string; scheduled_at: string; status: string; }
export interface MatchedClient { client_id: string; client_name: string; match_score: number; match_reason: string; }
export interface CampaignBriefing { id: string; user_id: string; campaign_type: string; headline: string; listing_url?: string; key_intel: { [key: string]: string }; original_draft: string; edited_draft?: string; matched_audience: MatchedClient[]; status: 'new' | 'launched' | 'dismissed'; }

interface AppContextType {
  loading: boolean;
  isAuthenticated: boolean;
  user: User | null;
  clients: Client[];
  properties: Property[];
  conversations: Conversation[];
  nudges: CampaignBriefing[];
  logout: () => void;
  api: {
    get: (endpoint: string) => Promise<any>;
    post: (endpoint: string, body: any) => Promise<any>;
    put: (endpoint: string, body: any) => Promise<any>;
    del: (endpoint: string) => Promise<any>;
  };
  // MODIFIED: The login function now returns the User object or null.
  login: (token: string) => Promise<User | null>;
  loginAndRedirect: (token: string) => Promise<boolean>;
  fetchDashboardData: () => Promise<void>;
  updateClientInList: (updatedClient: Client) => void;
  refetchScheduledMessagesForClient: (clientId: string) => Promise<ScheduledMessage[]>;
  refreshUser: () => Promise<void>;
  
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
  const tokenRef = useRef<string | null>(null);
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
    router.replace('/auth/login');
  }, [router]);
  
  const api = useCallback(() => {
    const request = async (endpoint: string, method: string, body?: any) => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${baseUrl}${endpoint}`;
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (tokenRef.current) headers['Authorization'] = `Bearer ${tokenRef.current}`;
      const config: RequestInit = { method, headers, body: body ? JSON.stringify(body) : undefined };
      const response = await fetch(url, config);
      if (!response.ok) {
        if (response.status === 401) logout();
        const errorData = await response.json().catch(() => ({ detail: `API Error: ${response.statusText}` }));
        throw new Error(errorData.detail || 'An unknown error occurred');
      }
      const text = await response.text();
      return text ? JSON.parse(text) : {};
    };
    return {
      get: (endpoint: string) => request(endpoint, 'GET'),
      post: (endpoint: string, body: any) => request(endpoint, 'POST', body),
      put: (endpoint: string, body: any) => request(endpoint, 'PUT', body),
      del: (endpoint: string) => request(endpoint, 'DELETE'),
    };
  }, [logout]);

  const refreshUser = useCallback(async () => {
    try {
        const userData = await api().get('/api/users/me');
        setUser(userData);
    } catch (error) {
        console.error("Failed to refresh user data:", error);
        logout(); // If we can't get user data, log out
    }
  }, [api, logout]);

  // --- MODIFIED FUNCTION ---
  // The login function now fetches user data, sets state, and returns the
  // user object on success or null on failure.
  const login = useCallback(async (newToken: string): Promise<User | null> => {
    Cookies.set('auth_token', newToken, { expires: 7, path: '/' });
    tokenRef.current = newToken;
    try {
      const userData: User = await api().get('/api/users/me');
      setUser(userData);
      setIsAuthenticated(true);
      return userData; // Return the user data on success
    } catch (error) {
      console.error("Authentication failed:", error);
      logout();
      return null; // Return null on failure
    }
  }, [api, logout]);

  // --- MODIFIED FUNCTION ---
  // This function now uses the return value from `login` to decide where to
  // redirect the user, ensuring the correct initial navigation path.
  const loginAndRedirect = async (token: string): Promise<boolean> => {
      const loggedInUser = await login(token);

      if (loggedInUser) {
          if (loggedInUser.onboarding_complete) {
              router.push('/community');
          } else {
              router.push('/onboarding');
          }
          return true;
      }
      
      // If login fails, the login() function handles the logout/redirect.
      return false;
  };

  const fetchDashboardData = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const results = await Promise.allSettled([
        api().get('/api/clients'),
        api().get('/api/properties'),
        api().get('/api/conversations/'),
        api().get('/api/campaigns')
      ]);
      if (results[0].status === 'fulfilled') setClients(results[0].value);
      if (results[1].status === 'fulfilled') setProperties(results[1].value);
      if (results[2].status === 'fulfilled') setConversations(results[2].value);
      if (results[3].status === 'fulfilled') setNudges(results[3].value);
      results.forEach((result, index) => {
        if (result.status === 'rejected') console.error(`Failed to fetch endpoint ${index}:`, result.reason);
      });
    } catch (error) {
      console.error("A critical error occurred while fetching dashboard data:", error);
    }
  }, [api, isAuthenticated]);

  useEffect(() => {
    const checkUserSession = async () => {
      setLoading(true);
      const savedToken = Cookies.get('auth_token');
      if (savedToken) {
        // We only log in here to restore the session. No redirect is needed
        // as the AuthGuard will handle routing on initial page load.
        await login(savedToken);
      }
      setLoading(false);
    };
    checkUserSession();
  }, [login]); // The dependency on `login` is now safe.

  const updateClientInList = (updatedClient: Client) => {
    setClients(prevClients => prevClients.map(c => c.id === updatedClient.id ? updatedClient : c));
  };
  
  const refetchScheduledMessagesForClient = useCallback(async (clientId: string): Promise<ScheduledMessage[]> => {
    try {
      return await api().get(`/api/scheduled-messages/?client_id=${clientId}`);
    } catch (error) {
      console.error(`Failed to fetch scheduled messages for ${clientId}:`, error);
      return [];
    }
  }, [api]);

  const value: AppContextType = {
    loading,
    isAuthenticated,
    user,
    clients,
    properties,
    conversations,
    nudges,
    logout,
    api: api(),
    login,
    loginAndRedirect,
    fetchDashboardData,
    updateClientInList,
    refetchScheduledMessagesForClient,
    refreshUser,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) throw new Error('useAppContext must be used within an AppProvider');
  return context;
};