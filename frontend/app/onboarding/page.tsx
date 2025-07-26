// frontend/app/onboarding/page.tsx
// --- DEFINITIVE FIX V13 ---
// 1. Adds a check for `user.onboarding_complete` to the resumable state
//    useEffect. This prevents it from incorrectly redirecting the user
//    after they have successfully finished the final step.

'use client';

// Imports remain the same...
import { useState, useEffect, FC, Dispatch, SetStateAction, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAppContext } from '@/context/AppContext';
import { motion, AnimatePresence, Variants } from 'framer-motion';
import { Building, Handshake, ShoppingCart, CheckCircle, ArrowRight, UserPlus, Check, Search, Sparkles, Briefcase } from 'lucide-react';
import Confetti from 'react-confetti';
import { ACTIVE_THEME } from '@/utils/theme';
import Image from 'next/image';

// All sub-components (ProgressBar, Step1, Step2, etc.) remain unchanged...
const roles = [
    { key: 'realtor', icon: Building, title: 'Realtor', description: 'For those guiding big decisions.', workStyle: 'guiding_big_decisions', enabled: true },
    { key: 'therapist', icon: Handshake, title: 'Therapist / Coach', description: 'For those providing ongoing service.', workStyle: 'providing_ongoing_service', enabled: true },
    { key: 'retailer', icon: ShoppingCart, title: 'Retail / E-commerce', description: 'For those fulfilling specific needs.', workStyle: 'fulfilling_specific_needs', enabled: false },
];
const progressSteps = ['Style', 'Contacts', 'Activate'];
const stepVariants: Variants = {
  hidden: { opacity: 0, y: 30, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.4, ease: "easeOut" } },
  exit: { opacity: 0, y: -30, scale: 0.98, transition: { duration: 0.2, ease: "easeIn" } },
};
const ProgressBar: FC<{ currentStep: number }> = ({ currentStep }) => (
    <div className="flex justify-between items-center w-full max-w-sm mx-auto mb-8">
        {progressSteps.map((name, index) => {
            const stepIndex = index + 1;
            const isCompleted = currentStep > stepIndex;
            const isActive = currentStep === stepIndex;
            return (
                <div key={name} className="flex-1 flex items-center gap-2 last:flex-none">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${isCompleted ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-white' : isActive ? 'border-2 border-cyan-400 text-cyan-400' : 'bg-white/10 text-gray-400'}`}>
                        {isCompleted ? <Check size={16} /> : stepIndex}
                    </div>
                    <span className={`transition-colors duration-300 ${isActive || isCompleted ? 'text-white' : 'text-gray-500'}`}>{name}</span>
                    {stepIndex < progressSteps.length && <div className="flex-1 h-0.5 bg-white/10 mx-2" />}
                </div>
            );
        })}
    </div>
);
const Step1RoleSelection: FC<{ setStep: Dispatch<SetStateAction<number>> }> = ({ setStep }) => {
    const { api, refreshUser } = useAppContext();
    const [selectedRoleKey, setSelectedRoleKey] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const handleNext = async () => {
        if (!selectedRoleKey) return;
        const role = roles.find(r => r.key === selectedRoleKey);
        if (!role) return;
        setIsLoading(true);
        setError(null);
        try {
            await api.put('/api/users/me', { 
                user_type: role.key, 
                vertical: role.key === 'therapist' ? 'therapy' : 'real_estate',
                strategy: { work_style: role.workStyle }, 
                onboarding_state: { work_style_set: true } 
            });
            await refreshUser();
            setStep(2);
        } catch (err: any) {
            setError(err.message || 'Failed to save your role. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };
    return (
        <div className="bg-glass-card p-8 rounded-2xl">
            <h1 className="text-3xl font-bold text-center text-white mb-2">Welcome! How do you help your clients?</h1>
            <p className="text-center text-gray-400 mb-8">This choice helps your AI co-pilot learn the best way to engage your clients.</p>
            <div className="space-y-4 mb-8">
                {roles.map((role) => (
                    <button key={role.key} disabled={!role.enabled} onClick={() => setSelectedRoleKey(role.key)}
                        className={`relative w-full p-6 text-left border-2 rounded-xl transition-all duration-300 flex items-center gap-6 group ${selectedRoleKey === role.key ? 'bg-cyan-500/10 border-cyan-400 shadow-glow scale-105' : 'bg-white/5 border-transparent hover:border-cyan-400/50'} ${!role.enabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}>
                        {selectedRoleKey === role.key && <CheckCircle className="absolute top-4 right-4 w-6 h-6 text-cyan-400" />}
                        {!role.enabled && <span className="absolute top-4 right-4 text-xs font-bold bg-gray-500 text-white px-2 py-1 rounded-full">Coming Soon</span>}
                        <div className="p-3 bg-cyan-500/10 rounded-lg group-hover:scale-110 transition-transform"><role.icon className="w-10 h-10 text-cyan-400 flex-shrink-0" /></div>
                        <div><h3 className="text-xl font-bold text-white">{role.title}</h3><p className="text-gray-300">{role.description}</p></div>
                    </button>
                ))}
            </div>
            <button onClick={handleNext} disabled={!selectedRoleKey || isLoading} className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-400 to-blue-500 text-white font-bold py-4 rounded-lg text-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-button">
                {isLoading ? 'Saving...' : 'Continue'} {!isLoading && <ArrowRight className="w-5 h-5" />}
            </button>
            {error && <p className="text-red-400 text-center mt-4">{error}</p>}
        </div>
    );
};
const Step2ContactImport: FC<{ setStep: Dispatch<SetStateAction<number>> }> = ({ setStep }) => {
    const { api, token } = useAppContext();
    const [manualContact, setManualContact] = useState({ name: '', email: '', phone: '' });
    const [isLoading, setIsLoading] = useState(false);
    const [contactAdded, setContactAdded] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const handleManualAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        try {
            await api.post('/api/clients/manual', { full_name: manualContact.name, email: manualContact.email, phone_number: manualContact.phone });
            setContactAdded(true);
            setManualContact({ name: '', email: '', phone: '' });
            setTimeout(() => setContactAdded(false), 3000);
        } catch (err: any) {
            setError(err.message || 'Failed to add contact. Please check the backend.');
        } finally {
            setIsLoading(false);
        }
    };
    const handleGoogleImport = async () => {
        setIsLoading(true);
        setError(null);
        if (!token) {
            setError("Authentication token not found. Please log in again.");
            setIsLoading(false);
            return;
        }
        try {
            const response = await api.get(`/api/auth/google-oauth-url?state=${token}`);
            if (response.auth_url) {
                window.location.href = response.auth_url;
            } else {
                throw new Error("Could not retrieve Google authentication URL.");
            }
        } catch (err: any) {
            setError(err.message || "Failed to start Google import.");
            setIsLoading(false);
        }
    };
    return (
        <div className="bg-glass-card p-8 rounded-2xl">
            <h1 className="text-3xl font-bold text-center text-white mb-2">Now, let's bring in your people.</h1>
            <p className="text-center text-gray-400 mb-8">Import contacts to let your AI co-pilot find opportunities.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="flex flex-col space-y-4">
                    <button onClick={handleGoogleImport} disabled={isLoading} className="flex-1 p-6 text-left border-2 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-3 bg-white/5 hover:border-cyan-400/50 border-transparent hover:scale-105 disabled:opacity-50">
                        <div className="flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm">
                            <svg className="w-8 h-8" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white text-center">Import from Google</h3>
                            <p className="text-gray-400 text-center text-sm">Fastest way to get started.</p>
                        </div>
                    </button>
                    <button disabled className="flex-1 p-6 text-left border-2 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-3 bg-white/5 hover:border-cyan-400/50 border-transparent hover:scale-105 opacity-40 cursor-not-allowed">
                        <Briefcase className="w-10 h-10 text-cyan-400" />
                        <div>
                            <h3 className="text-xl font-bold text-white text-center">Import from Outlook</h3>
                            <p className="text-gray-400 text-center text-sm">Coming Soon.</p>
                        </div>
                    </button>
                </div>
                <div className="bg-black/20 p-6 rounded-xl border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-4">Add Manually</h3>
                    <form onSubmit={handleManualAdd} className="space-y-4">
                        <input type="text" placeholder="Full Name" value={manualContact.name} onChange={(e) => setManualContact({...manualContact, name: e.target.value})} className="w-full p-3 bg-white/10 rounded-md text-white placeholder-gray-400 border border-transparent focus:outline-none focus:ring-2 focus:ring-cyan-400" required />
                        <input type="tel" placeholder="Phone Number" value={manualContact.phone} onChange={(e) => setManualContact({...manualContact, phone: e.target.value})} className="w-full p-3 bg-white/10 rounded-md text-white placeholder-gray-400 border border-transparent focus:outline-none focus:ring-2 focus:ring-cyan-400" required />
                        <button type="submit" disabled={isLoading} className={`w-full flex items-center justify-center gap-2 text-white font-bold py-3 rounded-lg text-md transition-all ${contactAdded ? 'bg-green-600' : 'bg-white/10 hover:bg-white/20'} disabled:opacity-50`}>
                            {isLoading ? 'Adding...' : contactAdded ? <>Added <Check/></> : <>Add Contact <UserPlus/></>}
                        </button>
                    </form>
                </div>
            </div>
            {error && <p className="text-red-400 text-center mb-4">{error}</p>}
            <p className="text-xs text-center text-gray-500 mb-8">We never store your passwords and only access basic contact information.</p>
            <button onClick={() => setStep(3)} className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-400 to-blue-500 text-white font-bold py-4 rounded-lg text-lg hover:opacity-90 transition-all shadow-button">Continue<ArrowRight className="w-5 h-5" /></button>
        </div>
    );
};
const Step3ActivateNumber: FC<{ setStep: Dispatch<SetStateAction<number>> }> = ({ setStep }) => {
    const { api, refreshUser } = useAppContext();
    const [searchType, setSearchType] = useState<'areaCode' | 'zip'>('areaCode');
    const [searchValue, setSearchValue] = useState('');
    const [availableNumbers, setAvailableNumbers] = useState<any[]>([]);
    const [selectedNumber, setSelectedNumber] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const handleSearch = async () => {
        if (!searchValue) return;
        setIsLoading(true); setError(null);
        try {
            const params = new URLSearchParams();
            if (searchType === 'areaCode') params.append('area_code', searchValue);
            if (searchType === 'zip') params.append('zip_code', searchValue);
            const res = await api.get(`/api/twilio/numbers?${params.toString()}`);
            setAvailableNumbers(res.numbers || []);
            if (!res.numbers || res.numbers.length === 0) setError(`No local numbers found. Try another search.`);
        } catch (err: any) { setError(err.message || 'Failed to search for numbers.'); } finally { setIsLoading(false); }
    };
    const handleFinish = async () => {
        if (!selectedNumber) return;
        setIsLoading(true); setError(null);
        try {
            await api.post('/api/twilio/assign', { phone_number: selectedNumber });
            await api.put('/api/users/me', { onboarding_complete: true });
            await refreshUser();
            setStep(4);
        } catch (err: any) { setError(err.message || 'Failed to finalize setup.'); } finally { setIsLoading(false); }
    };
    return (
        <div className="bg-glass-card p-8 rounded-2xl">
            <h1 className="text-3xl font-bold text-center text-white mb-2">Activate Your AI Nudge Number</h1>
            <p className="text-center text-gray-400 mb-8">This dedicated number is used for sending and receiving all client messages.</p>
            <div className="flex bg-white/10 rounded-lg p-1 mb-4">
                <button onClick={() => { setSearchType('areaCode'); setSearchValue(''); }} className={`w-1/2 p-2 rounded-md font-bold transition-colors ${searchType === 'areaCode' ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-white' : 'text-gray-300 hover:bg-white/10'}`}>Area Code</button>
                <button onClick={() => { setSearchType('zip'); setSearchValue(''); }} className={`w-1/2 p-2 rounded-md font-bold transition-colors ${searchType === 'zip' ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-white' : 'text-gray-300 hover:bg-white/10'}`}>ZIP Code</button>
            </div>
            <div className="flex gap-4 mb-4">
                <input type="tel" placeholder={searchType === 'areaCode' ? 'e.g., 415' : 'e.g., 90210'} value={searchValue} onChange={(e) => setSearchValue(e.target.value.replace(/\D/g, ''))} className="flex-grow p-4 bg-white/10 rounded-md text-white text-lg placeholder-gray-400 border border-transparent focus:outline-none focus:ring-2 focus:ring-cyan-400" maxLength={searchType === 'areaCode' ? 3 : 5} />
                <button onClick={handleSearch} disabled={isLoading || !searchValue} className="px-6 flex items-center justify-center gap-2 bg-white/10 text-white font-bold rounded-lg hover:bg-white/20 transition-all disabled:opacity-50"><Search/></button>
            </div>
            {availableNumbers.length > 0 && <div className="space-y-3 my-6 max-h-48 overflow-y-auto pr-2">{availableNumbers.map(num => (<button key={num.phone_number} onClick={() => setSelectedNumber(num.phone_number)} className={`w-full p-4 text-center border-2 rounded-xl transition-all duration-200 text-lg font-mono ${selectedNumber === num.phone_number ? 'bg-cyan-500/10 border-cyan-400' : 'bg-white/5 border-transparent hover:border-cyan-400/50'}`}>{num.friendly_name}</button>))}</div>}
            {error && <p className="text-red-400 text-center my-4">{error}</p>}
            <button onClick={handleFinish} disabled={!selectedNumber || isLoading} className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-400 to-blue-500 text-white font-bold py-4 rounded-lg text-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-button">{isLoading ? 'Activating...' : 'Finish Setup'} <ArrowRight/></button>
        </div>
    );
};
const Step4Celebration: FC = () => {
    const router = useRouter();
    const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });
    useEffect(() => {
        const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);
    return (
        <>
            <Confetti 
                width={windowSize.width} 
                height={windowSize.height} 
                recycle={false} 
                numberOfPieces={500} 
                tweenDuration={8000} 
                colors={[
                    ACTIVE_THEME.primary.from, 
                    ACTIVE_THEME.primary.to, 
                    ACTIVE_THEME.accent, 
                    ACTIVE_THEME.action,
                    '#ffffff'
                ]} 
            />
            <div className="text-center p-8">
                <div className="inline-block p-4 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-full mb-6 ring-4 ring-cyan-500/20">
                    <Sparkles className="w-16 h-16 text-cyan-300" />
                </div>
                <div className="mb-6">
                    <Image 
                        src="/AI Nudge Logo.png" 
                        alt="AI Nudge" 
                        width={200} 
                        height={50} 
                        className="mx-auto"
                        priority 
                    />
                </div>
                <h1 className="text-4xl font-bold text-white mb-4">🎉 Welcome to AI Nudge!</h1>
                <p className="text-xl text-gray-300 mb-4">Your AI co-pilot is ready to find opportunities in your network.</p>
                <p className="text-lg text-gray-400 mb-8">Start discovering hidden connections and growing your business.</p>
                <button onClick={() => router.push('/community')} className="px-8 flex items-center mx-auto justify-center gap-2 bg-gradient-to-r from-cyan-400 to-blue-500 text-white font-bold py-4 rounded-lg text-lg hover:opacity-90 transition-all shadow-button">
                    Explore My Community <ArrowRight />
                </button>
            </div>
        </>
    );
};
const ImportCelebration: FC<{ onDismiss: () => void }> = ({ onDismiss }) => {
    const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });
    useEffect(() => {
        const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/50 backdrop-blur-sm"
        >
            <Confetti
                width={windowSize.width}
                height={windowSize.height}
                recycle={false}
                numberOfPieces={400}
                tweenDuration={5000}
                colors={[
                    ACTIVE_THEME.primary.from, 
                    ACTIVE_THEME.primary.to, 
                    ACTIVE_THEME.accent, 
                    ACTIVE_THEME.action,
                    '#ffffff'
                ]}
            />
            <motion.div
                initial={{ opacity: 0, y: 50, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.4, ease: "easeOut", delay: 0.2 }}
                className="text-center p-8 bg-glass-card rounded-2xl"
            >
                <div className="inline-block p-3 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-full mb-4 ring-4 ring-cyan-500/20">
                    <CheckCircle className="w-12 h-12 text-cyan-300" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-2">✅ Contacts Successfully Imported!</h2>
                <p className="text-lg text-gray-300 mb-4">Your network is now connected to AI Nudge.</p>
                <p className="text-sm text-gray-400 mb-6">Ready to discover opportunities in your contacts.</p>
                <button
                    onClick={onDismiss}
                    className="px-6 py-3 bg-gradient-to-r from-cyan-400 to-blue-500 text-white font-bold rounded-lg hover:opacity-90 transition-opacity"
                >
                    Continue Setup
                </button>
            </motion.div>
        </motion.div>
    );
};

export default function OnboardingPage() {
    return (
        <Suspense fallback={<div className="min-h-screen w-full bg-[#0C0F1F]" />}>
            <OnboardingComponent />
        </Suspense>
    );
}

function OnboardingComponent() {
  const [step, setStep] = useState(1);
  const { user, loading } = useAppContext();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [showCelebration, setShowCelebration] = useState(false);

  // --- MODIFIED: Added check for user.onboarding_complete ---
  useEffect(() => {
    if (loading || !user) {
      return;
    }

    // If onboarding is fully complete, don't change the step.
    // This allows the user to see the final celebration screen (Step 4).
    // The AuthGuard will handle redirecting them away from this page if they reload.
    if (user.onboarding_complete) {
        return;
    }

    const { onboarding_state } = user;
    if (onboarding_state.contacts_imported) {
      setStep(3);
    } else if (onboarding_state.work_style_set) {
      setStep(2);
    } else {
      setStep(1);
    }
  }, [user, loading]);

  useEffect(() => {
    if (searchParams.get('import_success') === 'true') {
      setShowCelebration(true);
      window.history.replaceState(null, '', '/onboarding');
    }
  }, [searchParams]);

  const renderStep = () => {
    switch (step) {
      case 1: return <Step1RoleSelection setStep={setStep} />;
      case 2: return <Step2ContactImport setStep={setStep} />;
      case 3: return <Step3ActivateNumber setStep={setStep} />;
      case 4: return <Step4Celebration />;
      default: return <Step1RoleSelection setStep={setStep} />;
    }
  };

  return (
    <main className="min-h-screen w-full bg-[#0C0F1F] flex flex-col items-center justify-center p-4 overflow-hidden relative">
      <div className="absolute inset-0 bg-grid-pattern opacity-30"></div>
      <div className="absolute inset-0 bg-radial-gradient"></div>

      <AnimatePresence>
        {showCelebration && <ImportCelebration onDismiss={() => setShowCelebration(false)} />}
      </AnimatePresence>
      
      <div className={`w-full max-w-2xl z-10 transition-filter duration-500 ${showCelebration ? 'blur-md' : 'blur-none'}`}>
        {step < 4 && <ProgressBar currentStep={step} />}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            variants={stepVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </div>
    </main>
  );
}