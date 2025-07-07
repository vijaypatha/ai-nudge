// frontend/components/client-intake/ProviderConnect.tsx
// DEFINITIVE FIX: Replaces the non-existent 'getGoogleAuthUrl' with the correct 'api.get' method.
"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAppContext } from "@/context/AppContext";
import Cookies from 'js-cookie';

const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21.35 11.1H12.18V13.83H18.68C18.36 17.64 15.19 19.27 12.19 19.27C8.61 19.27 6.07 16.34 6.07 12.81C6.07 9.28 8.53 6.35 12.19 6.35C13.86 6.35 15.63 7.23 16.34 8.16L18.28 6.48C16.43 4.91 14.28 4 12.19 4C7.59 4 4.02 7.58 4.02 12.19C4.02 16.8 7.59 20.38 12.19 20.38C17.9 20.38 21.52 16.42 21.52 11.33C21.52 10.95 21.43 10.53 21.35 10.1Z" fill="#FFFFFF"/>
  </svg>
);

export const ProviderConnect = () => {
  const { api } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Use a ref to get the current token without causing re-renders.
  const tokenRef = useRef<string | null>(null);
  useEffect(() => {
    tokenRef.current = Cookies.get('auth_token') || null;
  }, []);

  const handleConnect = async () => {
    if (!tokenRef.current) {
        setError("Your session is not ready. Please refresh and try again.");
        return;
    }
    setIsLoading(true);
    setError(null);
    try {
      // --- CORRECTED ---
      // The API call now uses the correct 'get' method and constructs the URL
      // with the token as the 'state' query parameter.
      const { auth_url } = await api.get(`/api/auth/google-oauth-url?state=${tokenRef.current}`);
      window.location.href = auth_url;
    } catch (err) {
      setError("Could not connect. Please try again.");
      setIsLoading(false);
      console.error(err);
    }
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleConnect}
        disabled={isLoading}
        className="inline-flex items-center justify-center gap-3 w-full h-12 px-6 font-semibold text-white transition-all duration-300 bg-gray-700/80 rounded-lg hover:bg-gray-700 focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white disabled:opacity-50"
      >
        <GoogleIcon />
        {isLoading ? "Redirecting..." : "Connect Google Account"}
      </button>
      {error && <p className="text-sm font-medium text-red-400 mt-2">{error}</p>}
    </div>
  );
};