// frontend/app/auth/callback/google/page.tsx
// --- DEFINITIVE FIX V3 ---
// 1. Calls refreshUser() after a successful import to prevent stale state.
// 2. Redirects to '/onboarding' instead of '/community' to continue the flow.
// 3. Adds '?import_success=true' to the URL to trigger a celebration message.

"use client";

import { useEffect, useState, Suspense, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { Loader2 } from 'lucide-react';

function GoogleCallback() {
  // --- MODIFIED: Added refreshUser ---
  const { api, loginAndRedirect, isAuthenticated, refreshUser } = useAppContext();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [status, setStatus] = useState("Finalizing authentication...");
  const [error, setError] = useState<string | null>(null);

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

    if (isAuthenticated && code && !hasProcessedCode.current) {
      hasProcessedCode.current = true;
      setStatus("Session verified. Importing your contacts...");
      
      api.post('/api/auth/google-callback', { code })
        // --- MODIFIED: Chained promises to refresh user state before redirecting ---
        .then(result => {
          setStatus("Finalizing import...");
          // Step 1: Refresh the user object in the context
          return refreshUser();
        })
        .then(() => {
          // Step 2: Now that user state is fresh, redirect back to onboarding
          setStatus("Import successful! Redirecting...");
          router.push('/onboarding?import_success=true');
        })
        .catch(err => {
          console.error("Backend callback handler failed:", err);
          const errorMessage = err.message || "An unexpected error occurred during import.";
          setError(errorMessage);
          setStatus("Error");
        });
    }

  // --- MODIFIED: Added refreshUser to dependency array ---
  }, [isAuthenticated, api, loginAndRedirect, router, searchParams, refreshUser]);

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

// --- MODIFIED: Wrapped in Suspense because useSearchParams requires it ---
export default function GoogleCallbackPage() {
    return (
        <Suspense>
            <GoogleCallback />
        </Suspense>
    );
}