// frontend/components/onboarding/ContactImportStep.tsx
// Purpose: A self-contained component for the "Contact Import" step of the onboarding flow.

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { ProviderConnect } from '@/components/client-intake/ProviderConnect';
import { ManualContactForm } from '@/components/client-intake/ManualContactForm';

export const ContactImportStep = ({ onComplete }: { onComplete: () => void }) => {
    const { user, api, refreshUser } = useAppContext();
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleFinish = async () => {
        setIsLoading(true);
        try {
            // Mark this step as complete.
            const updatedState = { ...user?.onboarding_state, contacts_imported: true, first_nudges_seen: true }; // Skipping nudge preview for now
            
            // Mark the entire onboarding as complete.
            await api.put('/api/users/me', {
                onboarding_state: updatedState,
                onboarding_complete: true
            });
            await refreshUser();
            router.push('/community'); // Redirect to the main app
        } catch (err) {
            console.error("Failed to finalize onboarding:", err);
            setIsLoading(false);
        }
    };

    return (
        <div className="animate-in fade-in-0 duration-500">
            <h1 className="text-4xl font-bold text-white text-center">Now let’s bring in your people.</h1>
            <p className="text-gray-400 mt-2 text-center">Import your contacts — we’ll clean, organize, and show you who’s ready to reconnect.</p>
            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
                <div className="p-6 bg-gray-900/50 rounded-lg border border-gray-700">
                    <h2 className="text-2xl font-bold text-white">Import from Google</h2>
                    <p className="text-gray-400 mt-1">This is the fastest way to get started.</p>
                    <div className="mt-6">
                        <ProviderConnect />
                    </div>
                    <p className="text-xs text-gray-500 mt-4">We'll redirect you back here after connecting.</p>
                </div>
                <div className="bg-gray-900/50 rounded-lg border border-gray-700">
                    <ManualContactForm />
                </div>
            </div>
            <div className="text-center mt-12">
                <button onClick={handleFinish} disabled={isLoading} className="btn-primary text-lg py-3 px-12">
                  {isLoading ? 'Finalizing...' : 'Finish & Go to My Community'}
                </button>
            </div>
        </div>
    );
};
