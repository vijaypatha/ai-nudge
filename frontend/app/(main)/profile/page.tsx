// frontend/app/(main)/profile/page.tsx
// --- UPDATED: Removed MLS username/password fields and related save logic.

"use client";

import { useState, useEffect, ChangeEvent, FC } from "react";
import { Trash2, Edit3, Save, XCircle, Loader2, User, Briefcase, Bot, LogOut, Sparkles } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { useAppContext, User as UserType } from '@/context/AppContext';
import { TimezoneSelector } from "@/components/ui/TimezoneSelector";
import { ContentDiscovery } from "@/components/profile/ContentDiscovery";
import { ContentResourceManager } from "@/components/profile/ContentResourceManager";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';


export interface FaqItem {
  id: string;
  question: string;
  answer: string;
  is_enabled: boolean;
  isNew?: boolean;
}

// --- HELPER COMPONENT: FaqCard (Unchanged) ---
const FaqCard: FC<{
  item: FaqItem;
  onUpdate: (id: string, data: Partial<FaqItem>) => Promise<void>;
  onRemove: (id: string) => void;
  isMasterEnabled: boolean;
}> = ({ item, onUpdate, onRemove, isMasterEnabled }) => {
  const [isEditing, setIsEditing] = useState(item.isNew || false);
  const [currentQuestion, setCurrentQuestion] = useState(item.question);
  const [currentAnswer, setCurrentAnswer] = useState(item.answer);

  const handleSave = () => {
    if (currentQuestion.trim() !== '' || currentAnswer.trim() !== '') {
       onUpdate(item.id, { question: currentQuestion, answer: currentAnswer, isNew: false });
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    if (item.isNew) {
        onRemove(item.id);
    } else {
      setCurrentQuestion(item.question);
      setCurrentAnswer(item.answer);
      setIsEditing(false);
    }
  };

  const baseInputStyles = "w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition text-sm";

  return (
    <div className={`flex flex-col w-full rounded-xl border bg-gray-800/40 p-5 transition-all ${isMasterEnabled && item.is_enabled ? 'border-white/20' : 'border-white/10 bg-gray-900/50'}`}>
      <div className="flex-grow">
        {isEditing ? (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-gray-400">Question</label>
              <input value={currentQuestion} onChange={(e) => setCurrentQuestion(e.target.value)} placeholder="Enter a common question..." className={`mt-1 ${baseInputStyles}`} />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-400">AI's Answer</label>
              <textarea value={currentAnswer} onChange={(e) => setCurrentAnswer(e.target.value)} placeholder="Enter the answer the AI should give..." rows={4} className={`mt-1 ${baseInputStyles} resize-none`} />
            </div>
          </div>
        ) : (
          <>
            <h3 className="font-semibold text-white mb-2">{item.question || "New FAQ"}</h3>
            <p className={`text-sm text-gray-300 whitespace-pre-wrap ${!item.answer ? 'italic text-gray-500' : ''}`}>
              {item.answer || "No answer provided."}
            </p>
          </>
        )}
      </div>
      <div className="flex justify-between items-center border-t border-white/10 pt-4 mt-4">
        <div className="flex items-center gap-2">
            <input type="checkbox" id={`enable-${item.id}`} checked={item.is_enabled} onChange={(e) => onUpdate(item.id, { is_enabled: e.target.checked })} disabled={!isMasterEnabled} className="h-4 w-4 rounded bg-gray-700 border-gray-600 text-teal-500 focus:ring-teal-500 disabled:opacity-50" />
            <label htmlFor={`enable-${item.id}`} className={`text-xs font-medium ${!isMasterEnabled ? 'text-gray-600' : 'text-gray-400'}`}>Active</label>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button onClick={handleCancel} className="px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5 text-gray-300 hover:bg-gray-700"><XCircle size={14} /> Cancel</button>
              <button onClick={handleSave} className="px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5 btn-primary"><Save size={14} /> Save</button>
            </>
          ) : (
            <>
              <button onClick={() => onRemove(item.id)} className="p-2 rounded-md text-red-400 hover:bg-red-500/10"><Trash2 size={16} /></button>
              <button onClick={() => setIsEditing(true)} className="p-2 rounded-md text-blue-400 hover:bg-blue-500/10"><Edit3 size={16} /></button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};


// --- MAIN PAGE COMPONENT ---
export default function ProfilePage() {
    const { api, user, loading: isContextLoading, logout, refreshUser } = useAppContext();
    const [profile, setProfile] = useState<UserType | null>(null);
    const [faqs, setFaqs] = useState<FaqItem[]>([]);
    const [isEditingProfile, setIsEditingProfile] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showConfetti, setShowConfetti] = useState(false);
    const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

    // Add window size tracking for confetti
    useEffect(() => {
        const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleProfileChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setProfile(p => p ? { ...p, [e.target.name]: e.target.value } : null);
    };

    // --- MODIFIED: Removed MLS fields from the save payload ---
    // frontend/app/(main)/profile/page.tsx
    const handleProfileSave = async (initialData?: Partial<UserType>) => {
        const dataToSave = initialData || profile;
        if (!dataToSave) return;
        
        setIsSaving(true);
        setError(null);
        
        try {
            // This payload now correctly includes the 'specialties' field
            const payload = {
                full_name: dataToSave.full_name,
                email: dataToSave.email,
                timezone: dataToSave.timezone,
                specialties: dataToSave.specialties, // This field is now correctly typed and included
                ...initialData
            };
            
            const updatedUser = await api.put('/api/users/me', payload);
            setProfile(updatedUser);
            await refreshUser();
            if (!initialData) setIsEditingProfile(false);
        } catch (err) {
            setError("Failed to save profile.");
            console.error(err);
        } finally {
            setIsSaving(false);
        }
    };
    
    useEffect(() => {
        if (user && !user.timezone) {
            const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            if (detectedTimezone) {
                handleProfileSave({ timezone: detectedTimezone });
            }
        }
    }, [user]);

    useEffect(() => {
        if (user) {
            setProfile(user);
        }
    }, [user]);

    useEffect(() => {
        if (isContextLoading) return;
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const faqData = await api.get('/api/faqs/');
                setFaqs(faqData);
            } catch (err: any) {
                setError(err.message || "Could not load your settings.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [isContextLoading, api]);

    const handleMasterSwitchToggle = async (checked: boolean) => {
        if (!profile) return;
        const originalState = profile.faq_auto_responder_enabled;
        setProfile({ ...profile, faq_auto_responder_enabled: checked });
        try {
            await api.put('/api/users/me', { faq_auto_responder_enabled: checked });
        } catch (err) {
            setProfile({ ...profile, faq_auto_responder_enabled: originalState });
        }
    };

    const handleAddFaq = () => {
        setFaqs(prevFaqs => [{ id: uuidv4(), question: '', answer: '', is_enabled: true, isNew: true }, ...prevFaqs]);
    };

    const handleUpdateFaq = async (id: string, data: Partial<FaqItem>) => {
        const faq = faqs.find(f => f.id === id);
        if (!faq) return;
        const isNew = faq.isNew;
        const payload = { question: faq.question, answer: faq.answer, ...data };

        try {
            if (isNew) {
                await api.post('/api/faqs/', payload);
                // Show confetti for new FAQ
                setShowConfetti(true);
                setTimeout(() => setShowConfetti(false), 7000);
            } else {
                await api.put(`/api/faqs/${id}`, payload);
            }
            const freshFaqs = await api.get('/api/faqs/');
            setFaqs(freshFaqs);
        } catch (err) {
            setError("Failed to update FAQ.");
        }
    };

    const handleRemoveFaq = async (id: string) => {
        const isNew = faqs.find(f => f.id === id)?.isNew;
        if (isNew) {
            setFaqs(faqs.filter(f => f.id !== id));
            return;
        }
        try {
            await api.del(`/api/faqs/${id}`);
            setFaqs(faqs.filter(f => f.id !== id));
        } catch (err) {
            setError("Failed to remove FAQ.");
        }
    };

    // --- MODIFIED: Removed the MLS fields from the JSX for 'realtor' user type ---
    // frontend/app/(main)/profile/page.tsx
    const renderBusinessDetails = () => {
        if (!profile) return null;
        switch(profile.user_type) {
            case 'realtor':
                return <p className="text-sm text-gray-400">Your MLS connection is managed automatically by the system.</p>;
            
            case 'therapist':
                // The new component is rendered here, passing state down
                return (
                    <ContentDiscovery 
                        initialSpecialties={profile.specialties || []}
                        onSpecialtiesChange={(newSpecialties) => {
                            setProfile(p => p ? { ...p, specialties: newSpecialties } : null)
                        }}
                    />
                );
            default:
                return <p className="text-sm text-gray-500">No business-specific settings available for this user type.</p>;
        }
    };

    if (isLoading || isContextLoading) return <div className="flex items-center justify-center h-screen bg-gray-900"><Loader2 className="animate-spin h-8 w-8 text-teal-500" /></div>;
    if (error && !profile) return <div className="p-8 text-center text-red-400 bg-gray-900">{error}</div>;
    if (!profile) return null;

    return (
        <>
            {/* Confetti for successful FAQ additions */}
            {showConfetti && (
                <Confetti
                    width={windowSize.width}
                    height={windowSize.height}
                    recycle={false}
                    numberOfPieces={600}
                    tweenDuration={7000}
                    colors={[
                        ACTIVE_THEME.primary.from,
                        ACTIVE_THEME.primary.to,
                        ACTIVE_THEME.accent,
                        ACTIVE_THEME.action,
                        '#ffffff'
                    ]}
                />
            )}

            <main className="flex-1 overflow-y-auto bg-gray-900 text-white p-6 md:p-8 lg:p-12">
                <div className="max-w-4xl mx-auto space-y-12">
                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <div className="flex justify-between items-center mb-6">
                            <h1 className="text-2xl font-bold text-white flex items-center gap-3"><User /> My Profile</h1>
                            <div className="flex items-center gap-2">
                                <button onClick={logout} className="px-4 py-2 text-sm font-semibold flex items-center gap-2 bg-gray-700/50 hover:bg-gray-700 rounded-md">
                                   <LogOut size={16}/> Logout
                                </button>
                                <button onClick={() => isEditingProfile ? handleProfileSave() : setIsEditingProfile(true)} disabled={isSaving} className="btn-primary px-4 py-2 text-sm font-semibold flex items-center gap-2">
                                    {isSaving ? <><Loader2 className="h-4 w-4 animate-spin" />Saving...</> : (isEditingProfile ? <><Save size={16}/>Save Profile</> : <><Edit3 size={16}/>Edit Profile</>)}
                                </button>
                            </div>
                        </div>
                        <div className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-1"><label className="text-sm font-medium text-gray-400">Full Name</label><input name="full_name" value={profile.full_name || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50" /></div>
                                <div className="space-y-1"><label className="text-sm font-medium text-gray-400">Contact Phone</label><input value={profile.phone_number || ''} disabled={true} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed" /></div>
                                <div className="space-y-1"><label className="text-sm font-medium text-gray-400">Email Address</label><input name="email" type="email" value={profile.email || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50" /></div>
                                <div className="space-y-1"><label className="text-sm font-medium text-gray-400">My Default Time Zone</label>
                                    <TimezoneSelector value={profile.timezone || ''} onChange={handleProfileChange} disabled={!isEditingProfile} />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3"><Briefcase /> Business Details</h2>
                        {renderBusinessDetails()}
                    </div>
                    
                    {/* Theme Switcher Section */}
                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">🎨 App Theme</h2>
                        <p className="text-sm text-gray-400 mb-4">Choose your preferred color scheme for the entire app.</p>
                        <ThemeSwitcher />
                    </div>
                    
                    {/* Content Resources Section */}
                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <ContentResourceManager api={api} />
                    </div>
                    
                    {/* AI Nudge AutoPilot Section */}
                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <div className="flex justify-between items-center mb-2">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Bot className="text-cyan-400" />
                                AI Nudge AutoPilot
                            </h2>
                            <button onClick={handleAddFaq} className="px-3 py-1.5 text-sm font-semibold bg-white/10 rounded-lg hover:bg-white/20 flex items-center gap-2">
                                <Sparkles className="w-4 h-4" />
                                + Add FAQ
                            </button>
                        </div>
                        <p className="text-sm text-gray-400 mb-6">
                            Train your AI co-pilot to answer common questions instantly and maintain your authentic voice.
                        </p>
                        <div className="flex items-center space-x-3 p-4 rounded-lg bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 mb-8">
                            <input 
                                type="checkbox" 
                                id="master-faq-toggle" 
                                checked={profile.faq_auto_responder_enabled} 
                                onChange={(e) => handleMasterSwitchToggle(e.target.checked)} 
                                className="h-4 w-4 rounded bg-white/10 border-white/20 text-cyan-500 focus:ring-cyan-500" 
                            />
                            <label htmlFor="master-faq-toggle" className="text-base font-medium text-white">
                                Enable AI Nudge AutoPilot
                            </label>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {faqs.map(faq => (
                                <FaqCard 
                                    key={faq.id} 
                                    item={faq} 
                                    onUpdate={handleUpdateFaq} 
                                    onRemove={handleRemoveFaq} 
                                    isMasterEnabled={profile.faq_auto_responder_enabled || false} 
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        </>
    );
}