// frontend/app/onboarding/page.tsx
// DEFINITIVE FIX: This page is now a controller that dynamically renders the
// correct onboarding step based on the user's progress.

"use client";

import { useAppContext } from '@/context/AppContext';
import { WorkStyleStep } from '@/components/onboarding/WorkStyleStep';
import { ContactImportStep } from '@/components/onboarding/ContactImportStep';
import { Sparkles } from 'lucide-react';

export default function OnboardingPage() {
  const { user, loading, refreshUser } = useAppContext();

  // Show a loading screen while the user context is being fetched.
  if (loading || !user) {
    return (
      <main className="min-h-screen w-full flex items-center justify-center bg-brand-dark">
        <Sparkles className="w-10 h-10 text-brand-accent animate-spin" />
      </main>
    );
  }

  // This function determines which step component to render.
  const renderCurrentStep = () => {
    // For now, we are skipping phone verification and nudge preview as per the plan.
    // The logic can be easily extended here.
    if (!user.onboarding_state.work_style_set) {
      return <WorkStyleStep onComplete={refreshUser} />;
    }
    if (!user.onboarding_state.contacts_imported) {
      return <ContactImportStep onComplete={refreshUser} />;
    }
    // If all steps are complete, this page shouldn't be visible due to AuthGuard,
    // but as a fallback, we can show a completion message.
    return <div>Onboarding complete! Redirecting...</div>;
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-brand-dark text-gray-200 p-4">
      <div className="w-full max-w-4xl p-8 bg-brand-dark/50 border border-white/10 rounded-2xl shadow-2xl">
        {renderCurrentStep()}
      </div>
    </main>
  );
}
