// frontend/app/onboarding/page.tsx
"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { Building, Stethoscope, Handshake, ArrowRight } from 'lucide-react';
import clsx from 'clsx';

type Step = 'welcome' | 'vertical' | 'details';
type UserType = 'realtor' | 'therapist' | 'loan_officer';

const VerticalCard = ({ icon, title, value, onClick, isSelected }: { icon: React.ReactNode, title: string, value: UserType, onClick: (value: UserType) => void, isSelected: boolean }) => (
  <button
    type="button"
    onClick={() => onClick(value)}
    className={clsx(
      "p-6 w-full text-left border rounded-lg transition-all transform hover:scale-105",
      isSelected ? "bg-emerald-500/20 border-emerald-500 shadow-lg" : "bg-gray-700/50 hover:bg-gray-700 border-gray-600"
    )}
  >
    <div className="flex items-center gap-4">
      <div className={clsx("p-3 rounded-full", isSelected ? "bg-emerald-500/20" : "bg-gray-600/50")}>{icon}</div>
      <div>
        <h3 className={clsx("text-lg font-bold", isSelected ? "text-emerald-300" : "text-white")}>{title}</h3>
      </div>
    </div>
  </button>
);

export default function OnboardingPage() {
  const { user, api } = useAppContext();
  const router = useRouter();
  const [step, setStep] = useState<Step>('welcome');
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const payload: any = {
        full_name: formData.full_name,
        user_type: formData.user_type,
      };

      if (formData.user_type === 'realtor') {
        payload.mls_username = formData.mls_username;
        payload.mls_password = formData.mls_password;
      } else if (formData.user_type === 'therapist') {
        payload.license_number = formData.license_number;
      }

      await api.put('/users/me', payload);
      window.location.href = '/dashboard'; // Force reload to update user context fully
    } catch (err) {
      setError('Failed to save profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const renderStep = () => {
    switch (step) {
      case 'welcome':
        return (
            <>
              <h1 className="text-3xl font-bold text-white">Welcome, {formData.full_name || 'there'}!</h1>
              <p className="text-gray-400 mt-2">Let's start by getting your name right.</p>
              <div className="mt-8">
                <label htmlFor="full_name" className="text-sm font-semibold text-gray-400 mb-2 block">Full Name</label>
                <input id="full_name" name="full_name" type="text" required value={formData.full_name} onChange={handleInputChange} className="w-full input-field" />
              </div>
              <button type="button" onClick={() => setStep('vertical')} disabled={!formData.full_name} className="w-full btn-primary text-lg py-3 mt-8">Continue <ArrowRight className="inline w-5 h-5"/></button>
            </>
        );
      case 'vertical':
        return (
            <>
              <h1 className="text-3xl font-bold text-white">What is your profession?</h1>
              <p className="text-gray-400 mt-2">This helps us tailor your AI co-pilot.</p>
              <div className="mt-8 space-y-4">
                  <VerticalCard icon={<Building className="w-6 h-6 text-emerald-400"/>} title="Realtor" value="realtor" onClick={handleVerticalSelect} isSelected={formData.user_type === 'realtor'} />
                  <VerticalCard icon={<Stethoscope className="w-6 h-6 text-emerald-400"/>} title="Therapist" value="therapist" onClick={handleVerticalSelect} isSelected={formData.user_type === 'therapist'} />
                  <VerticalCard icon={<Handshake className="w-6 h-6 text-emerald-400"/>} title="Loan Officer" value="loan_officer" onClick={handleVerticalSelect} isSelected={formData.user_type === 'loan_officer'} />
              </div>
              <button type="button" onClick={() => setStep('details')} disabled={!formData.user_type} className="w-full btn-primary text-lg py-3 mt-8">Continue <ArrowRight className="inline w-5 h-5"/></button>
            </>
        );
      case 'details':
        return (
          <form onSubmit={handleSubmit}>
            <h1 className="text-3xl font-bold text-white">Final Details</h1>
            <p className="text-gray-400 mt-2">Just a few more things to get you connected.</p>
            <div className="mt-8 space-y-6">
              {formData.user_type === 'realtor' && (
                <div className="p-4 bg-gray-700/50 rounded-lg space-y-4 border border-gray-600">
                  <h3 className="font-semibold text-white">MLS Connection</h3>
                  <div><label htmlFor="mls_username" className="text-sm text-gray-400 mb-2 block">MLS Username</label><input id="mls_username" name="mls_username" type="text" value={formData.mls_username} onChange={handleInputChange} className="w-full input-field"/></div>
                  <div><label htmlFor="mls_password" className="text-sm text-gray-400 mb-2 block">MLS Password</label><input id="mls_password" name="mls_password" type="password" value={formData.mls_password} onChange={handleInputChange} className="w-full input-field"/></div>
                </div>
              )}
              {formData.user_type === 'therapist' && (
                <div className="p-4 bg-gray-700/50 rounded-lg space-y-4 border border-gray-600">
                  <h3 className="font-semibold text-white">Practice Details</h3>
                  <div><label htmlFor="license_number" className="text-sm text-gray-400 mb-2 block">License Number</label><input id="license_number" name="license_number" type="text" value={formData.license_number} onChange={handleInputChange} className="w-full input-field"/></div>
                </div>
              )}
              {error && <p className="text-sm text-center text-red-400">{error}</p>}
              <button type="submit" disabled={isLoading} className="w-full btn-primary text-lg py-3">{isLoading ? 'Saving...' : 'Complete Setup'}</button>
            </div>
          </form>
        );
    }
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-gray-900 text-gray-200 p-4">
      <div className="w-full max-w-lg p-8 space-y-6 bg-gray-800 rounded-2xl shadow-lg text-center">
        {renderStep()}
      </div>
    </main>
  );
}