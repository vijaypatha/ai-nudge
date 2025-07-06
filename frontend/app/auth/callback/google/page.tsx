// frontend/app/auth/callback/google/page.tsx
"use client";

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';

function GoogleCallback() {
  const { api, login, isAuthenticated } = useAppContext();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [status, setStatus] = useState("Finalizing authentication...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state'); // The 'state' parameter now contains our auth token
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(`Authentication was denied by Google: ${errorParam}.`);
      setStatus("Error");
      return;
    }

    // If we are not yet authenticated but have a token in the state, log in first.
    if (state && !isAuthenticated) {
        setStatus("Verifying your session...");
        login(state).then(() => {
            // After login completes, the component will re-render, and this
            // useEffect will run again. On the next run, `isAuthenticated` will be true.
            console.log("Session restored from state token.");
        });
        return; // Return here to wait for the re-render after login.
    }

    // Once we are authenticated AND we have the code from Google, proceed.
    if (isAuthenticated && code) {
      setStatus("Session verified. Processing Google sign-in...");
      
      api.handleGoogleCallback(code)
        .then(result => {
          setStatus("Import successful! Redirecting to your dashboard...");
          const { imported_count, merged_count } = result;
          router.push(`/dashboard?imported=${imported_count}&merged=${merged_count}`);
        })
        .catch(err => {
          console.error("Backend callback handler failed:", err);
          const errorMessage = err.response?.data?.detail || "An unexpected error occurred during import.";
          setError(errorMessage);
          setStatus("Error");
        });
    }

  }, [isAuthenticated, api, login, router, searchParams]);

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-background">
      <div className="text-center p-4">
        {status !== "Error" ? (
          <div className="text-2xl font-semibold">AI Nudge</div>
        ) : (
          <div className="text-2xl font-semibold text-destructive">Authentication Failed</div>
        )}
        <p className="mt-2 text-muted-foreground">{error || status}</p>
        {error && (
            <button 
                onClick={() => router.push('/onboarding')}
                className="mt-4 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium h-10 px-4 py-2 border">
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