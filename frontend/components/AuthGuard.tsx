// frontend/components/AuthGuard.tsx
// DEFINITIVE FIX: This version uses the new `onboarding_complete` flag from the
// user object to enforce the onboarding flow.

"use client";

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { Sparkles } from 'lucide-react';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, loading } = useAppContext();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Don't do anything while the context is loading its initial state.
    if (loading) {
      return;
    }

    // If the user is not authenticated, redirect them to the login page.
    // Exception: Allow access to the login page itself.
    if (!isAuthenticated && pathname !== '/auth/login') {
      console.log("AuthGuard: Not authenticated, redirecting to login.");
      router.push('/auth/login');
      return;
    }

    // If the user is authenticated but has NOT completed onboarding,
    // redirect them to the onboarding page.
    // Exception: Allow access to the onboarding page itself.
    if (isAuthenticated && user && !user.onboarding_complete && pathname !== '/onboarding') {
      console.log("AuthGuard: Onboarding not complete, redirecting to onboarding.");
      router.push('/onboarding');
      return;
    }

  }, [isAuthenticated, user, loading, router, pathname]);

  // While loading, show a full-screen spinner to prevent content flashing.
  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-screen text-brand-text-muted bg-brand-dark">
        <Sparkles className="w-10 h-10 text-brand-accent animate-spin mb-4" />
        <p className="text-xl font-medium">Authenticating...</p>
      </div>
    );
  }

  // If authenticated and onboarding is complete (or they are on the onboarding page), render the children.
  if (isAuthenticated && (user?.onboarding_complete || pathname === '/onboarding')) {
    return <>{children}</>;
  }

  // If on the login page, render it.
  if (!isAuthenticated && pathname === '/auth/login') {
      return <>{children}</>;
  }

  // Otherwise, render nothing while the redirect is in progress.
  return null;
}
