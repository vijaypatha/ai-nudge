"use client";

import { useState, useEffect, useRef, ChangeEvent, KeyboardEvent, ClipboardEvent } from 'react';
import Image from 'next/image';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { CheckCircle, Bot } from 'lucide-react';

// --- The contents of this file are the same as the previous login page component ---
// --- No changes are needed to the logic itself ---

const ValuePropItem = ({ children }: { children: React.ReactNode }) => (
    <li className="flex items-center gap-3 text-left">
        <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
        <span className="text-gray-300">{children}</span>
    </li>
);

const MultiBoxInput = ({ length, onChange }: { length: number, onChange: (value: string) => void }) => {
    // ... (MultiBoxInput component code remains the same) ...
};

export default function LoginForm() {
    const [step, setStep] = useState<'phone' | 'otp'>('phone');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [otp, setOtp] = useState('');
    const [fullPhoneNumber, setFullPhoneNumber] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAppContext();
    const router = useRouter();
    const searchParams = useSearchParams();
    const isSignup = searchParams.get('action') === 'signup';

    const handleDevLogin = async () => { /* ... */ };
    const handlePhoneSubmit = async (e: React.FormEvent) => { /* ... */ };
    const handleOtpSubmit = async (e: React.FormEvent) => { /* ... */ };

  return (
    <main className="min-h-screen w-full grid grid-cols-1 lg:grid-cols-2 bg-animated-gradient">
        <div className="flex flex-col justify-center p-8 lg:p-12 text-white order-1 lg:order-1">
            {/* ... Value Prop Panel JSX ... */}
        </div>
        <div className="flex items-center justify-center p-8 bg-gray-900/50 backdrop-blur-sm order-2 lg:order-2">
            <div className="w-full max-w-sm mx-auto">
                <div className="text-center mb-10">
                    {/* ... Form Header JSX ... */}
                </div>
                {step === 'phone' ? (
                  <form onSubmit={handlePhoneSubmit} className="space-y-6">
                    {/* ... Phone Form JSX ... */}
                  </form>
                ) : (
                  <form onSubmit={handleOtpSubmit} className="space-y-6">
                    {/* ... OTP Form JSX ... */}
                  </form>
                )}
                {/* ... Error and Dev Login JSX ... */}
            </div>
        </div>
    </main>
  );
}

// NOTE: To save space, the full component code from the last step is omitted here,
// but you should paste the entire content of the previous `LoginPage` component
// and rename it to `LoginForm`.