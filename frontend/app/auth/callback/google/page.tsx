// frontend/app/auth/callback/google/page.tsx
// --- DEFINITIVE FIX V2 ---
// 1. Added a `useRef` flag (hasProcessedCode) to the `useEffect` hook.
// 2. This prevents the component from making multiple POST requests to the
//    backend with the same one-time-use code, fixing the "invalid_grant" error.

"use client";

import { useEffect, useState, Suspense, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { Loader2 } from 'lucide-react';

function GoogleCallback() {
  const { api, loginAndRedirect, isAuthenticated } = useAppContext();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [status, setStatus] = useState("Finalizing authentication...");
  const [error, setError] = useState<string | null>(null);

  // --- ADDED: useRef flag to prevent duplicate API calls ---
  const hasProcessedCode = useRef(false);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(`Authentication was denied by Google: ${errorParam}.`);
      setStatus("Error");
      return;
    }

    if (state && !isAuthenticated) {
        setStatus("Restoring your session...");
        loginAndRedirect(state).then((success) => {
            if (!success) {
                setError("Failed to restore session from token.");
                setStatus("Error");
            }
        });
        return; // Wait for re-render after session is restored
    }

    // --- MODIFIED: Added check for hasProcessedCode.current ---
    if (isAuthenticated && code && !hasProcessedCode.current) {
      // Set the flag to true immediately to prevent re-entry
      hasProcessedCode.current = true;
      
      setStatus("Session verified. Processing Google sign-in...");
      
      api.post('/api/auth/google-callback', { code })
        .then(result => {
          setStatus("Import successful! Redirecting...");
          const { imported_count, merged_count } = result;
          // Redirect to the community page with query params for the celebration view.
          router.push(`/community?imported=${imported_count}&merged=${merged_count}`);
        })
        .catch(err => {
          console.error("Backend callback handler failed:", err);
          const errorMessage = err.message || "An unexpected error occurred during import.";
          setError(errorMessage);
          setStatus("Error");
        });
    }

  }, [isAuthenticated, api, loginAndRedirect, router, searchParams]);

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-gray-900 text-white">
      <div className="text-center p-4">
        {status !== "Error" ? (
          <Loader2 className="w-12 h-12 animate-spin text-teal-400" />
        ) : (
          <div className="text-2xl font-semibold text-red-500">Authentication Failed</div>
        )}
        <p className="mt-4 text-lg text-gray-400">{error || status}</p>
        {error && (
            <button 
                onClick={() => router.push('/onboarding')}
                className="mt-6 px-6 py-2 text-sm font-semibold bg-white/10 rounded-md hover:bg-white/20">
                Return to Onboarding
            </button>
        )}
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
    return (
        <Suspense>
            <GoogleCallback />
        </Suspense>
    );
}