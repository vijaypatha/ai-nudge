// frontend/app/onboarding/page.tsx
"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { Building, Stethoscope, Handshake, ArrowRight } from 'lucide-react';
import clsx from 'clsx';

// This is the new component for the "Connect Google" button.
// We'll create this in the next step.
import { ProviderConnect } from '@/components/client-intake/ProviderConnect';

type Step = 'profile' | 'connect';
type UserType = 'realtor' | 'therapist' | 'loan_officer';

// Your existing VerticalCard component - no changes needed.
const VerticalCard = ({ icon, title, value, onClick, isSelected }: { icon: React.ReactNode, title: string, value: UserType, onClick: (value: UserType) => void, isSelected: boolean }) => (
  <button
    type="button"
    onClick={() => onClick(value)}
    className={clsx(
      "p-4 w-full text-left border rounded-lg transition-all transform hover:scale-[1.02]",
      isSelected ? "bg-emerald-500/20 border-emerald-500 shadow-lg" : "bg-gray-700/50 hover:bg-gray-700 border-gray-600"
    )}
  >
    <div className="flex items-center gap-4">
      <div className={clsx("p-3 rounded-full bg-opacity-20", isSelected ? "bg-emerald-500" : "bg-gray-600")}>{icon}</div>
      <h3 className={clsx("text-lg font-bold", isSelected ? "text-emerald-300" : "text-white")}>{title}</h3>
    </div>
  </button>
);

export default function OnboardingPage() {
  const { user, api } = useAppContext();
  const router = useRouter();
  const [step, setStep] = useState<Step>('connect'); //profile or connect
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    user_type: '' as UserType | '',
    mls_username: '',
    mls_password: '',
    license_number: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleVerticalSelect = (vertical: UserType) => {
    setFormData(prev => ({ ...prev, user_type: vertical }));
  };

  const handleFinalSubmit = async () => {
    // This function now only saves profile details and redirects.
    // The client import is handled separately by the ProviderConnect component.
    setIsLoading(true);
    setError('');
    try {
      const payload: any = {
        full_name: formData.full_name,
        user_type: formData.user_type,
      };

      if (formData.user_type === 'realtor') payload.mls_username = formData.mls_username;
      if (formData.user_type === 'therapist') payload.license_number = formData.license_number;

      await api.put('/users/me', payload);
      router.push('/dashboard'); // Go to dashboard after finishing.
    } catch (err) {
      setError('Failed to save profile. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-gray-900 text-gray-200 p-4">
      <div className="w-full max-w-4xl p-8 bg-gray-800 rounded-2xl shadow-2xl">
        
        {/* STEP 1: Profile Information */}
        {step === 'profile' && (
          <div className="max-w-lg mx-auto text-center">
            <h1 className="text-4xl font-bold text-white">Welcome to AI Nudge</h1>
            <p className="text-gray-400 mt-2">Let's set up your AI co-pilot in two quick steps.</p>
            
            <div className="mt-8 text-left space-y-6">
              <div>
                <label htmlFor="full_name" className="text-sm font-semibold text-gray-400 mb-2 block">First, what's your full name?</label>
                <input id="full_name" name="full_name" type="text" required value={formData.full_name} onChange={handleInputChange} className="w-full input-field" placeholder="e.g., Jane Doe"/>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-400 mb-2 block">And what is your profession?</label>
                <div className="space-y-3">
                  <VerticalCard icon={<Building className="w-6 h-6 text-emerald-400"/>} title="Realtor" value="realtor" onClick={handleVerticalSelect} isSelected={formData.user_type === 'realtor'} />
                  <VerticalCard icon={<Stethoscope className="w-6 h-6 text-emerald-400"/>} title="Therapist" value="therapist" onClick={handleVerticalSelect} isSelected={formData.user_type === 'therapist'} />
                  <VerticalCard icon={<Handshake className="w-6 h-6 text-emerald-400"/>} title="Loan Officer" value="loan_officer" onClick={handleVerticalSelect} isSelected={formData.user_type === 'loan_officer'} />
                </div>
              </div>
            </div>

            <button type="button" onClick={() => setStep('connect')} disabled={!formData.full_name || !formData.user_type} className="w-full btn-primary text-lg py-3 mt-10">
              Continue <ArrowRight className="inline w-5 h-5"/>
            </button>
          </div>
        )}

        {/* STEP 2: Connect Tools & Final Details */}
        {step === 'connect' && (
          <div>
            <h1 className="text-4xl font-bold text-white text-center">Connect your business</h1>
            <p className="text-gray-400 mt-2 text-center">Import clients to activate your AI, and confirm your details.</p>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
              
              {/* Primary Action: Client Import */}
              <div className="p-6 bg-gray-900/50 rounded-lg border border-gray-700">
                <h2 className="text-2xl font-bold text-white">Import Your Clients</h2>
                <p className="text-gray-400 mt-1">This is the fastest way to get started.</p>
                <div className="mt-6">
                  {/* The ProviderConnect component will live here */}
                  <ProviderConnect />
                </div>
                <p className="text-xs text-gray-500 mt-4">You can add more sources later from your settings.</p>
              </div>

              {/* Secondary Action: Final Details */}
              <div className="p-6">
                <h2 className="text-2xl font-bold text-white">Confirm Your Details</h2>
                <p className="text-gray-400 mt-1">Add details to tailor your AI's knowledge.</p>
                
                <div className="mt-6 space-y-4">
                  {formData.user_type === 'realtor' && (
                    <>
                      <h3 className="font-semibold text-emerald-400">MLS Connection</h3>
                      <div><label htmlFor="mls_username" className="text-sm text-gray-400 mb-1 block">MLS Username</label><input id="mls_username" name="mls_username" type="text" value={formData.mls_username} onChange={handleInputChange} className="w-full input-field"/></div>
                      <div><label htmlFor="mls_password" className="text-sm text-gray-400 mb-1 block">MLS Password</label><input id="mls_password" name="mls_password" type="password" value={formData.mls_password} onChange={handleInputChange} className="w-full input-field"/></div>
                    </>
                  )}
                  {formData.user_type === 'therapist' && (
                     <>
                      <h3 className="font-semibold text-emerald-400">Practice Details</h3>
                      <div><label htmlFor="license_number" className="text-sm text-gray-400 mb-1 block">License Number</label><input id="license_number" name="license_number" type="text" value={formData.license_number} onChange={handleInputChange} className="w-full input-field"/></div>
                    </>
                  )}
                  {/* Add fields for 'loan_officer' if needed */}
                  {error && <p className="text-sm text-center text-red-400">{error}</p>}
                </div>

                <button onClick={handleFinalSubmit} disabled={isLoading} className="w-full btn-primary text-lg py-3 mt-8">
                  {isLoading ? 'Saving...' : 'Finish & Go to Dashboard'}
                </button>
              </div>

            </div>
          </div>
        )}

      </div>
    </main>
  );
}