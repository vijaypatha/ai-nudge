// frontend/app/auth/login/login-form.tsx
// DEFINITIVE FIX: This is the full 178-line file, updated to use the
// robust `loginAndRedirect` function from the context.

"use client";

import { useState, useEffect, useRef, ChangeEvent, KeyboardEvent, ClipboardEvent } from 'react';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { CheckCircle, Bot } from 'lucide-react';

const ValuePropItem = ({ children }: { children: React.ReactNode }) => (
    <li className="flex items-center gap-3 text-left">
        <CheckCircle className="w-5 h-5 text-teal-400 flex-shrink-0" />
        <span className="text-gray-300">{children}</span>
    </li>
);

const MultiBoxInput = ({ length, onChange }: { length: number, onChange: (value: string) => void }) => {
    const [values, setValues] = useState<string[]>(new Array(length).fill(""));
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
    useEffect(() => { inputRefs.current[0]?.focus(); }, []);
    const handleChange = (element: HTMLInputElement, index: number) => {
        const value = element.value.replace(/[^0-9]/g, '');
        if (value) {
            const newValues = [...values];
            newValues[index] = value;
            setValues(newValues);
            onChange(newValues.join(''));
            if (index < length - 1) inputRefs.current[index + 1]?.focus();
        }
    };
    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>, index: number) => {
        if (e.key === "Backspace") {
            const newValues = [...values];
            if (newValues[index]) {
                newValues[index] = "";
                setValues(newValues);
                onChange(newValues.join(''));
            } else if (index > 0) {
                inputRefs.current[index - 1]?.focus();
            }
        }
    };
    const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
        e.preventDefault();
        const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length);
        if (paste) {
            const newValues = new Array(length).fill("");
            for (let i = 0; i < paste.length; i++) newValues[i] = paste[i];
            setValues(newValues);
            onChange(newValues.join(''));
            const focusIndex = Math.min(paste.length, length - 1);
            inputRefs.current[focusIndex]?.focus();
        }
    };
    return (
        <div className="flex justify-center gap-1.5 md:gap-2" onPaste={handlePaste}>
            {values.map((data, index) => (
                 <input
                    key={index} type="text" inputMode="numeric" maxLength={1} value={data}
                    ref={(el) => { inputRefs.current[index] = el; }}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => handleChange(e.target, index)}
                    onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => handleKeyDown(e, index)}
                    className="w-8 h-12 md:w-10 md:h-14 text-center text-xl font-bold bg-gray-700/50 border-2 border-gray-600 rounded-lg text-white focus:border-teal-500 focus:ring-teal-500 focus:outline-none transition"
                />
            ))}
        </div>
    );
};

export default function LoginForm() {
    const [step, setStep] = useState<'phone' | 'otp'>('phone');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [otp, setOtp] = useState('');
    const [fullPhoneNumber, setFullPhoneNumber] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { loginAndRedirect, api } = useAppContext();
    const searchParams = useSearchParams();
    const isSignup = searchParams.get('action') === 'signup';

    const handleDevLogin = async () => {
        setIsLoading(true);
        setError('');
        try {
            const demoUserId = "a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a";
            const data = await api.post('/api/auth/dev-login', { user_id: demoUserId });
            if (data.access_token) {
                await loginAndRedirect(data.access_token);
            } else {
                throw new Error('Access token not found in dev-login response.');
            }
        } catch (err: any) {
            setError("Developer login failed. Ensure backend is in development mode.");
            setIsLoading(false);
        }
    };

    const handlePhoneSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        const cleanedNumber = phoneNumber.replace(/\D/g, '');
        const formattedPhoneNumber = `+1${cleanedNumber}`;
        try {
            await api.post('/api/auth/otp/send', { phone_number: formattedPhoneNumber });
            setFullPhoneNumber(formattedPhoneNumber);
            setStep('otp');
        } catch (err: any) {
            setError('Failed to send code. Please check the number.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleOtpSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            const data = await api.post('/api/auth/otp/verify', { phone_number: fullPhoneNumber, otp_code: otp });
            if (data.access_token) {
                await loginAndRedirect(data.access_token);
            } else {
                throw new Error('Verification failed.');
            }
        } catch (err: any) {
            setError('Invalid code. Please try again.');
            setIsLoading(false);
        }
    };

    return (
      <main className="min-h-screen w-full flex flex-col lg:grid lg:grid-cols-2 bg-animated-gradient">
          <div className="flex flex-col justify-center p-8 lg:p-12 text-white order-1 lg:order-1">
              <div className="max-w-md mx-auto">
                  <div className="mb-12"><Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={200} height={40} /></div>
                  <div className="space-y-8 my-12 lg:my-0 text-center lg:text-left">
                      <h1 className="text-4xl font-bold leading-tight">From data to deals, automatically.</h1>
                      <ul className="space-y-4 text-lg inline-block"><ValuePropItem>Find hidden opportunities in your existing contacts.</ValuePropItem><ValuePropItem>Save 10+ hours a week on manual follow-up.</ValuePropItem><ValuePropItem>Engage clients with personalized, AI-drafted messages.</ValuePropItem></ul>
                  </div>
                  <p className="text-gray-500 text-sm mt-12 pt-8 border-t border-white/10 lg:absolute lg:bottom-8">&copy; {new Date().getFullYear()} AI Nudge. All rights reserved.</p>
              </div>
          </div>
          <div className="flex items-center justify-center p-8 bg-gray-900/50 backdrop-blur-sm order-2 lg:order-2">
              <div className="w-full max-w-sm mx-auto">
                  <div className="text-center mb-10">
                      <h2 className="text-3xl font-bold text-white">{isSignup ? "Create Your Account" : "Welcome Back"}</h2>
                      <p className="text-gray-400 mt-2">{step === 'phone' ? 'Enter your 10-digit phone number.' : `Enter the code we sent to ${fullPhoneNumber}.`}</p>
                  </div>
                  {step === 'phone' ? (
                    <form onSubmit={handlePhoneSubmit} className="space-y-6"><MultiBoxInput length={10} onChange={setPhoneNumber} /><button type="submit" disabled={isLoading || phoneNumber.length < 10} className="w-full btn-primary text-lg py-3">{isLoading ? 'Sending...' : 'Continue'}</button></form>
                  ) : (
                    <form onSubmit={handleOtpSubmit} className="space-y-6"><MultiBoxInput length={6} onChange={setOtp} /><button type="submit" disabled={isLoading || otp.length < 6} className="w-full btn-primary text-lg py-3">{isLoading ? 'Verifying...' : 'Continue'}</button></form>
                  )}
                  {error && <p className="text-sm text-center text-red-400 mt-4">{error}</p>}
                  {process.env.NODE_ENV === 'development' && (<div className="text-center mt-6"><button onClick={handleDevLogin} className="text-xs text-gray-500 hover:text-teal-400 flex items-center gap-2 mx-auto"><Bot size={14}/> Developer Login</button></div>)}
              </div>
          </div>
      </main>
    );
}