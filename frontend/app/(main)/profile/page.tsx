// File Path: frontend/app/profile/page.tsx
// ---
// FINAL, CORRECTED VERSION: This file is now completely self-contained.
// - All custom component imports (@/components, @/lib) have been removed.
// - All elements are now standard HTML (<button>, <input>, etc.) styled with Tailwind CSS.
// - All API calls now use the standard browser `fetch` function.
// ---

"use client";

import { useState, useEffect, ChangeEvent, FC } from "react";
import { Trash2, Edit3, Save, XCircle, Loader2, User, Briefcase, Bot } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { useAppContext } from '@/context/AppContext';


// --- TYPE DEFINITIONS ---
interface UserProfile {
    id: string;
    user_type: 'realtor' | 'therapist' | 'loan_officer';
    full_name: string;
    phone_number: string;
    email?: string;
    mls_username?: string;
    mls_password?: string;
    license_number?: string;
    faq_auto_responder_enabled: boolean;
}

export interface FaqItem {
  id: string;
  question: string;
  answer: string;
  is_enabled: boolean;
  isNew?: boolean;
}

// --- HELPER COMPONENT: FaqCard (defined in-file, using standard HTML) ---
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
    if (item.isNew) onRemove(item.id);
    else {
      setCurrentQuestion(item.question);
      setCurrentAnswer(item.answer);
      setIsEditing(false);
    }
  };

  const baseInputStyles = "w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-brand-accent focus:ring-1 focus:ring-brand-accent transition text-sm";

  return (
    <div className={`flex flex-col w-full rounded-xl border bg-brand-primary/50 p-5 transition-all ${isMasterEnabled && item.is_enabled ? 'border-white/20' : 'border-white/5 bg-brand-dark'}`}>
      <div className="flex-grow">
        {isEditing ? (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-brand-text-muted">Question</label>
              <input value={currentQuestion} onChange={(e) => setCurrentQuestion(e.target.value)} placeholder="Enter a common question..." className={`mt-1 ${baseInputStyles}`} />
            </div>
            <div>
              <label className="text-xs font-semibold text-brand-text-muted">AI's Answer</label>
              <textarea value={currentAnswer} onChange={(e) => setCurrentAnswer(e.target.value)} placeholder="Enter the answer the AI should give..." rows={4} className={`mt-1 ${baseInputStyles} resize-none`} />
            </div>
          </div>
        ) : (
          <>
            <h3 className="font-semibold text-white mb-2">{item.question || "New FAQ"}</h3>
            <p className={`text-sm text-brand-text-main whitespace-pre-wrap ${!item.answer ? 'italic text-brand-text-muted' : ''}`}>
              {item.answer || "No answer provided."}
            </p>
          </>
        )}
      </div>
      <div className="flex justify-between items-center border-t border-white/10 pt-4 mt-4">
        <div className="flex items-center gap-2">
            <input type="checkbox" id={`enable-${item.id}`} checked={item.is_enabled} onChange={(e) => onUpdate(item.id, { is_enabled: e.target.checked })} disabled={!isMasterEnabled} className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent disabled:opacity-50" />
            <label htmlFor={`enable-${item.id}`} className={`text-xs font-medium ${!isMasterEnabled ? 'text-brand-text-muted/50' : 'text-brand-text-muted'}`}>Active</label>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button onClick={handleCancel} className="px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5 text-slate-300 hover:bg-slate-700"><XCircle size={14} /> Cancel</button>
              <button onClick={handleSave} className="px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5 bg-primary-action hover:brightness-110 text-brand-dark font-semibold"><Save size={14} /> Save</button>
            </>
          ) : (
            <>
              <button onClick={() => onRemove(item.id)} className="p-2 rounded-md text-red-400 hover:bg-red-500/10"><Trash2 size={16} /></button>
              <button onClick={() => setIsEditing(true)} className="p-2 rounded-md text-blue-300 hover:bg-blue-500/10"><Edit3 size={16} /></button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// --- MAIN PAGE COMPONENT ---
export default function ProfilePage() {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isEditingProfile, setIsEditingProfile] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [faqs, setFaqs] = useState<FaqItem[]>([]);

    const API_BASE_URL = 'http://localhost:8001';

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const [userRes, faqRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/users/me`),
                    fetch(`${API_BASE_URL}/faqs/`)
                ]);
                if (!userRes.ok || !faqRes.ok) throw new Error("Failed to fetch initial data.");
                
                const userData = await userRes.json();
                const faqData = await faqRes.json();
                
                setProfile(userData);
                setFaqs(faqData);
            } catch (err: any) {
                setError(err.message || "Could not load your settings.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleApiCall = async (method: string, endpoint: string, body?: object) => {
        try {
            const options: RequestInit = {
                method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (body) options.body = JSON.stringify(body);
            
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            if (!response.ok) throw new Error(`API request failed: ${response.statusText}`);
            
            return response.status !== 204 ? await response.json() : null;
        } catch (err: any) {
            console.error(`API call failed for ${method} ${endpoint}:`, err);
            setError(err.message);
            throw err;
        }
    };

    const handleProfileChange = (e: ChangeEvent<HTMLInputElement>) => {
        setProfile(p => p ? { ...p, [e.target.name]: e.target.value } : null);
    };

    const handleProfileSave = async () => {
        if (!profile) return;
        setIsSaving(true);
        const { mls_password, ...rest } = profile;
        const payload = (mls_password && mls_password.trim()) ? profile : rest;
        
        try {
            const updatedProfile = await handleApiCall('PUT', '/users/me', payload);
            setProfile(updatedProfile);
            setIsEditingProfile(false);
        } catch (err) {
            // Error state is already set by handleApiCall
        } finally {
            setIsSaving(false);
        }
    };

    const handleMasterSwitchToggle = async (checked: boolean) => {
        if (!profile) return;
        const originalState = profile.faq_auto_responder_enabled;
        setProfile({ ...profile, faq_auto_responder_enabled: checked });
        try {
            await handleApiCall('PUT', '/users/me', { faq_auto_responder_enabled: checked });
        } catch (err) {
            setProfile({ ...profile, faq_auto_responder_enabled: originalState });
        }
    };

    const handleAddFaq = () => setFaqs(p => [{ id: uuidv4(), question: '', answer: '', is_enabled: true, isNew: true }, ...p]);

    const handleUpdateFaq = async (id: string, data: Partial<FaqItem>) => {
        const faq = faqs.find(f => f.id === id);
        if (!faq) return;
        const isNew = faq.isNew;
        const payload = { ...faq, ...data };
        try {
            isNew ? await handleApiCall('POST', '/faqs/', payload) : await handleApiCall('PUT', `/faqs/${id}`, payload);
            const freshFaqs = await handleApiCall('GET', '/faqs/');
            setFaqs(freshFaqs);
        } catch (err) {}
    };

    const handleRemoveFaq = async (id: string) => {
        const isNew = faqs.find(f => f.id === id)?.isNew;
        if (isNew) {
            setFaqs(faqs.filter(f => f.id !== id));
            return;
        }
        try {
            await handleApiCall('DELETE', `/faqs/${id}`);
            setFaqs(faqs.filter(f => f.id !== id));
        } catch (err) {}
    };

    const renderBusinessDetails = () => {
        if (!profile) return null;
        const inputStyles = "w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-brand-accent focus:ring-1 focus:ring-brand-accent transition text-sm disabled:opacity-50";
        switch(profile.user_type) {
            case 'realtor':
                return (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-1"><label className="text-sm font-medium text-brand-text-muted">MLS Username</label><input name="mls_username" value={profile.mls_username || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className={inputStyles} /></div>
                        <div className="space-y-1"><label className="text-sm font-medium text-brand-text-muted">MLS Password</label><input name="mls_password" type="password" placeholder="••••••••" onChange={handleProfileChange} disabled={!isEditingProfile} className={inputStyles} /></div>
                    </div>
                );
            default:
                return <p className="text-sm text-brand-text-muted">No business-specific settings available for this user type.</p>;
        }
    };

    if (isLoading) return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin h-8 w-8 text-brand-accent" /></div>;
    if (error && !profile) return <p className="text-red-400 p-8 text-center">{error}</p>;

    return (
        <div className="min-h-screen bg-brand-dark text-white py-12 px-4">
            <div className="max-w-4xl mx-auto space-y-12">
                <div className="bg-brand-primary rounded-xl border border-white/10 p-8">
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="text-2xl font-bold text-white flex items-center gap-3"><User /> My Profile</h1>
                        <button onClick={isEditingProfile ? handleProfileSave : () => setIsEditingProfile(true)} disabled={isSaving} className="px-4 py-2 text-sm font-semibold bg-primary-action text-brand-dark rounded-lg hover:brightness-110 disabled:opacity-50 flex items-center gap-2">
                            {isSaving ? <><Loader2 className="h-4 w-4 animate-spin" />Saving...</> : (isEditingProfile ? "Save Profile" : "Edit Profile")}
                        </button>
                    </div>
                    {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-1"><label className="text-sm font-medium text-brand-text-muted">Full Name</label><input name="full_name" value={profile?.full_name || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50" /></div>
                            <div className="space-y-1"><label className="text-sm font-medium text-brand-text-muted">Contact Phone (for Login)</label><input value={profile?.phone_number || ''} disabled={true} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-brand-text-muted cursor-not-allowed" /></div>
                            <div className="space-y-1 md:col-span-2"><label className="text-sm font-medium text-brand-text-muted">Email Address (Optional)</label><input name="email" type="email" value={profile?.email || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50" /></div>
                        </div>
                    </div>
                </div>
                <div className="bg-brand-primary rounded-xl border border-white/10 p-8">
                    <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3"><Briefcase /> Business Details</h2>
                    {renderBusinessDetails()}
                </div>
                <div className="bg-brand-primary rounded-xl border border-white/10 p-8">
                    <div className="flex justify-between items-center mb-2"><h2 className="text-2xl font-bold text-white flex items-center gap-3"><Bot />AI Auto-Responder</h2><button onClick={handleAddFaq} className="px-3 py-1.5 text-sm font-semibold bg-white/10 rounded-lg hover:bg-white/20">+ Add FAQ</button></div>
                    <p className="text-sm text-brand-text-muted mb-6">Train your AI to answer common questions instantly.</p>
                    <div className="flex items-center space-x-3 p-4 rounded-lg bg-white/5 mb-8">
                        <input type="checkbox" id="master-faq-toggle" checked={profile?.faq_auto_responder_enabled} onChange={(e) => handleMasterSwitchToggle(e.target.checked)} className="h-4 w-4 rounded bg-white/10 border-white/20 text-brand-accent focus:ring-brand-accent" />
                        <label htmlFor="master-faq-toggle" className="text-base font-medium">Enable AI Auto-Responder</label>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {faqs.map(faq => (<FaqCard key={faq.id} item={faq} onUpdate={handleUpdateFaq} onRemove={handleRemoveFaq} isMasterEnabled={profile?.faq_auto_responder_enabled || false} />))}
                    </div>
                </div>
            </div>
        </div>
    );
}