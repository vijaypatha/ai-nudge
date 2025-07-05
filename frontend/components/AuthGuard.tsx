// frontend/components/AuthGuard.tsx
// single "security checkpoint" for the entire authenticated part of our app.
"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { Sparkles } from 'lucide-react';

// --- ADDED: Helper to check if user profile is complete ---
// We consider the profile complete if they have selected a user_type.
const isProfileComplete = (user: any) => {
  return user && user.user_type;
};

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, loading } = useAppContext();
  const router = useRouter();

  useEffect(() => {
    // Don't do anything while the context is loading its state.
    if (loading) {
      return;
    }

    // If not authenticated, redirect to the login page.
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    // If authenticated but the profile is not complete, redirect to onboarding.
    if (isAuthenticated && !isProfileComplete(user)) {
      router.push('/onboarding');
      return;
    }

  }, [isAuthenticated, user, loading, router]);

  // While loading, show a full-screen spinner.
  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-screen text-brand-text-muted bg-brand-dark">
        <Sparkles className="w-10 h-10 text-brand-accent animate-spin mb-4" />
        <p className="text-xl font-medium">Authenticating...</p>
      </div>
    );
  }

  // If authenticated and profile is complete, render the requested page.
  if (isAuthenticated && isProfileComplete(user)) {
    return <>{children}</>;
  }

  // Otherwise, render nothing while the redirect happens.
  return null;
}