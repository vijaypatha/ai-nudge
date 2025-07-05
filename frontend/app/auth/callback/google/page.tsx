// frontend/app/auth/callback/google/page.tsx
"use client";

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';

function GoogleCallback() {
  const { api } = useAppContext();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [status, setStatus] = useState("Processing authentication...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(`Authentication failed: ${errorParam}. Please try again.`);
      setStatus("Error");
      return;
    }

    if (code) {
      api.handleGoogleCallback(code)
        .then(result => {
          setStatus("Import successful! Redirecting...");
          
          // --- DEFINITIVE FIX ---
          // Redirect to the dashboard and pass the import results as URL query
          // parameters. This allows the dashboard to trigger our celebration.
          const { imported_count, merged_count } = result;
          router.push(`/dashboard?imported=${imported_count}&merged=${merged_count}`);

        })
        .catch(err => {
          console.error("Callback handler failed:", err);
          const errorMessage = err.response?.data?.detail || "An unexpected error occurred during import.";
          setError(errorMessage);
          setStatus("Error");
        });
    } else {
        setError("Authorization code not found in URL. Please try again.");
        setStatus("Error");
    }
  }, [api, searchParams, router]);

  // This UI is shown briefly while the backend processes the import.
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

// The Suspense wrapper is required by Next.js for useSearchParams()
export default function GoogleCallbackPage() {
    return (
        <Suspense>
            <GoogleCallback />
        </Suspense>
    );
}
