// frontend/components/onboarding/WorkStyleStep.tsx
// Purpose: A self-contained component for the "Work Style" step of the onboarding flow.

'use client';

import { useState } from 'react';
import { Building, Stethoscope, Handshake, ArrowRight } from 'lucide-react';
import clsx from 'clsx';
import { useAppContext } from '@/context/AppContext';

type UserType = 'realtor' | 'therapist' | 'loan_officer';

const VerticalCard = ({ icon, title, value, onClick, isSelected }: { icon: React.ReactNode, title: string, value: UserType, onClick: (value: UserType) => void, isSelected: boolean }) => (
  <button
    type="button"
    onClick={() => onClick(value)}
    className={clsx(
      "p-4 w-full text-left border rounded-lg transition-all transform hover:scale-[1.02]",
      isSelected ? "bg-emerald-500/20 border-emerald-500 shadow-lg" : "bg-gray-800/80 hover:bg-gray-700/80 border-gray-700"
    )}
  >
    <div className="flex items-center gap-4">
      <div className={clsx("p-3 rounded-full bg-opacity-20", isSelected ? "bg-emerald-500" : "bg-gray-600")}>{icon}</div>
      <h3 className={clsx("text-lg font-bold", isSelected ? "text-emerald-300" : "text-white")}>{title}</h3>
    </div>
  </button>
);

export const WorkStyleStep = ({ onComplete }: { onComplete: () => void }) => {
    const { user, api, refreshUser } = useAppContext();
    const [isLoading, setIsLoading] = useState(false);
    const [formData, setFormData] = useState({
        full_name: user?.full_name || '',
        user_type: (user?.user_type as UserType) || '' as UserType | '',
    });

    const handleVerticalSelect = (vertical: UserType) => {
        setFormData(prev => ({ ...prev, user_type: vertical }));
    };

    const handleContinue = async () => {
        if (!formData.user_type) return;
        setIsLoading(true);
        try {
            const updatedState = { ...user?.onboarding_state, work_style_set: true };
            await api.put('/api/users/me', {
                user_type: formData.user_type,
                onboarding_state: updatedState
            });
            await refreshUser(); // Refresh user data in context
            onComplete(); // Notify parent to move to the next step
        } catch (err) {
            console.error("Failed to save work style:", err);
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-lg mx-auto text-center animate-in fade-in-0 duration-500">
            <h1 className="text-4xl font-bold text-white">How do you usually work with clients?</h1>
            <p className="text-gray-400 mt-2">This helps us tailor the AI to fit you — not the other way around.</p>
            <div className="mt-8 text-left space-y-6">
                <div>
                    <label className="text-sm font-semibold text-gray-400 mb-2 block">Select your profession</label>
                    <div className="space-y-3">
                        <VerticalCard icon={<Building className="w-6 h-6 text-emerald-400"/>} title="Realtor" value="realtor" onClick={handleVerticalSelect} isSelected={formData.user_type === 'realtor'} />
                        <VerticalCard icon={<Stethoscope className="w-6 h-6 text-emerald-400"/>} title="Therapist" value="therapist" onClick={handleVerticalSelect} isSelected={formData.user_type === 'therapist'} />
                        <VerticalCard icon={<Handshake className="w-6 h-6 text-emerald-400"/>} title="Loan Officer" value="loan_officer" onClick={handleVerticalSelect} isSelected={formData.user_type === 'loan_officer'} />
                    </div>
                </div>
            </div>
            <button type="button" onClick={handleContinue} disabled={!formData.user_type || isLoading} className="w-full btn-primary text-lg py-3 mt-10">
                {isLoading ? 'Saving...' : 'Continue'} <ArrowRight className="inline w-5 h-5"/>
            </button>
        </div>
    );
};
