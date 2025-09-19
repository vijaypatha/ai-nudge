"use client";

import { useState, useEffect, ChangeEvent, FC } from "react";
import { 
  Trash2, Edit3, Save, XCircle, Loader2, User, Briefcase, Bot, LogOut, 
  Sparkles, Library, Palette, MessageSquareQuote, ChevronDown, Check, 
  Users, Settings, Shield, Zap, Eye, EyeOff, Plus, Info, HelpCircle
} from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { useAppContext, User as UserType } from '@/context/AppContext';
import { TimezoneSelector } from "@/components/ui/TimezoneSelector";
import { ContentDiscovery } from "@/components/profile/ContentDiscovery";
import { ContentResourceManager, ContentResource } from "@/components/profile/ContentResourceManager";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { RoleManager } from "@/components/settings/RoleManager";
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';

export interface FaqItem {
  id: string;
  question: string;
  answer: string;
  is_enabled: boolean;
  isNew?: boolean;
}

// CORRECTED: Card component with your app's color scheme
const Card: FC<{ 
  children: React.ReactNode; 
  className?: string;
  variant?: 'default' | 'elevated' | 'bordered';
}> = ({ children, className = '', variant = 'default' }) => {
  const variantStyles = {
    // Updated to match your app's navy blue color scheme
    default: 'bg-slate-800/40 border-slate-600/20',
    elevated: 'bg-gradient-to-br from-slate-800/60 to-slate-900/80 border-slate-600/30 shadow-xl',
    bordered: 'bg-slate-800/30 border-teal-500/30 shadow-lg shadow-teal-500/10'
  };

  return (
    <div className={`backdrop-blur-sm rounded-2xl border transition-all duration-300 ${variantStyles[variant]} ${className}`}>
      {children}
    </div>
  );
};

// CORRECTED: Major Section with consistent colors
const MajorSection: FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}> = ({ icon, title, description, children }) => (
  <section className="mb-20">
    <Card variant="elevated" className="overflow-hidden">
      {/* Updated header colors to match your app */}
      <div className="bg-gradient-to-r from-slate-800/80 to-slate-900/60 border-b border-slate-600/20 p-8">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-teal-500/20 to-cyan-500/20 text-teal-400">
            {icon}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
            <p className="text-lg text-slate-300 leading-relaxed max-w-3xl">{description}</p>
          </div>
        </div>
      </div>
      
      <div className="p-8">
        {children}
      </div>
    </Card>
  </section>
);

// CORRECTED: SubSection with consistent colors
const SubSection: FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}> = ({ icon, title, description, children, action, className = '' }) => (
  <div className={`space-y-6 ${className}`}>
    <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          {icon && (
            <div className="p-2 rounded-lg bg-slate-700/50 text-slate-300">
              {icon}
            </div>
          )}
          <h2 className="text-xl font-semibold text-white">{title}</h2>
        </div>
        {description && (
          <p className="text-slate-400 text-base leading-relaxed max-w-2xl">{description}</p>
        )}
      </div>
      {action && (
        <div className="flex-shrink-0">
          {action}
        </div>
      )}
    </div>
    <div className="pl-0 lg:pl-11">
      {children}
    </div>
  </div>
);

// CORRECTED: Input styles matching your app's color scheme
const baseInputStyles = `
  w-full bg-slate-900/80 border border-slate-600/60 rounded-lg px-4 py-3 text-white text-base
  placeholder-slate-400 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 
  transition-all duration-200 hover:border-slate-500/80 focus:bg-slate-900
`;

// CORRECTED: Toggle Switch with consistent colors
const ToggleSwitch: FC<{
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label: string;
  description?: string;
}> = ({ id, checked, onChange, disabled, label, description }) => (
  <div className="p-6 rounded-xl bg-gradient-to-r from-teal-500/10 to-cyan-500/10 border border-teal-500/30">
    <div className="flex items-start gap-4">
      <div className="relative">
        <input
          type="checkbox"
          id={id}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <label
          htmlFor={id}
          className={`
            flex h-7 w-12 cursor-pointer rounded-full transition-colors duration-200
            ${checked ? 'bg-teal-500' : 'bg-slate-600'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-80'}
          `}
        >
          <span
            className={`
              h-6 w-6 rounded-full bg-white shadow-lg transition-transform duration-200 m-0.5
              ${checked ? 'translate-x-5' : 'translate-x-0'}
            `}
          />
        </label>
      </div>
      <div className="flex-1">
        <label htmlFor={id} className="text-xl font-semibold text-white cursor-pointer block mb-1">
          {label}
        </label>
        {description && (
          <p className="text-base text-slate-300 leading-relaxed">{description}</p>
        )}
      </div>
    </div>
  </div>
);

// CORRECTED: FAQ Card with consistent colors
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

  return (
    <Card 
      variant={isMasterEnabled && item.is_enabled ? 'elevated' : 'default'}
      className={`p-6 transition-all duration-300 hover:shadow-lg ${
        isMasterEnabled && item.is_enabled ? 'ring-1 ring-teal-500/30' : ''
      }`}
    >
      <div className="space-y-6">
        <div className="flex-grow">
          {isEditing ? (
            <div className="space-y-5">
              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Question
                </label>
                <input 
                  value={currentQuestion} 
                  onChange={(e) => setCurrentQuestion(e.target.value)} 
                  placeholder="What's a common question clients ask?" 
                  className={baseInputStyles} 
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  AI Response
                </label>
                <textarea 
                  value={currentAnswer} 
                  onChange={(e) => setCurrentAnswer(e.target.value)} 
                  placeholder="How should the AI respond to this question..." 
                  rows={4} 
                  className={`${baseInputStyles} resize-none`} 
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <h3 className="text-lg font-semibold text-white leading-tight pr-4">
                  {item.question || "New FAQ"}
                </h3>
                {item.is_enabled && isMasterEnabled && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-medium">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full"></div>
                    Active
                  </div>
                )}
              </div>
              <p className={`text-base text-slate-300 leading-relaxed ${
                !item.answer ? 'italic text-slate-500' : ''
              }`}>
                {item.answer || "No response configured yet."}
              </p>
            </div>
          )}
        </div>
        
        <div className="flex justify-between items-center pt-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3">
            <input 
              type="checkbox" 
              id={`enable-${item.id}`} 
              checked={item.is_enabled} 
              onChange={(e) => onUpdate(item.id, { is_enabled: e.target.checked })} 
              disabled={!isMasterEnabled} 
              className="h-4 w-4 rounded bg-slate-700 border-slate-600 text-teal-500 focus:ring-teal-500 disabled:opacity-50" 
            />
            <label 
              htmlFor={`enable-${item.id}`} 
              className={`text-sm font-medium ${
                !isMasterEnabled ? 'text-slate-600' : 'text-slate-300'
              }`}
            >
              Enable This Response
            </label>
          </div>
          
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <button 
                  onClick={handleCancel} 
                  className="px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 text-slate-300 hover:bg-slate-700/50 transition-colors"
                >
                  <XCircle size={16} /> Cancel
                </button>
                <button 
                  onClick={handleSave} 
                  className="px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 bg-teal-500 hover:bg-teal-600 text-white transition-colors"
                >
                  <Save size={16} /> Save
                </button>
              </>
            ) : (
              <>
                <button 
                  onClick={() => onRemove(item.id)} 
                  className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
                  title="Delete FAQ"
                >
                  <Trash2 size={18} />
                </button>
                <button 
                  onClick={() => setIsEditing(true)} 
                  className="p-2 rounded-lg text-blue-400 hover:bg-blue-500/10 transition-colors"
                  title="Edit FAQ"
                >
                  <Edit3 size={18} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

// Main Profile Page with CONSISTENT COLOR SCHEME
export default function ProfilePage() {
    const { api, user, clientRoles, loading: isContextLoading, logout, refreshUser } = useAppContext();
    const [profile, setProfile] = useState<UserType | null>(null);
    const [faqs, setFaqs] = useState<FaqItem[]>([]);
    const [contentResources, setContentResources] = useState<ContentResource[]>([]);
    const [isEditingProfile, setIsEditingProfile] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showConfetti, setShowConfetti] = useState(false);
    const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

    useEffect(() => {
        const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleProfileChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setProfile(p => p ? { ...p, [e.target.name]: e.target.value } : null);
    };

    const handleProfileSave = async (initialData?: Partial<UserType>) => {
        const dataToSave = initialData || profile;
        if (!dataToSave) return;
        setIsSaving(true);
        setError(null);
        try {
            const payload = {
                full_name: dataToSave.full_name,
                email: dataToSave.email,
                timezone: dataToSave.timezone,
                specialties: dataToSave.specialties,
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
                // Fetch FAQs and Content Resources in parallel
                const [faqData, resourceData] = await Promise.all([
                    api.get('/api/faqs/'),
                    api.get('/api/content-resources/')
                ]);
                setFaqs(faqData);
                setContentResources(resourceData);
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
        setFaqs(prevFaqs => [
            { id: uuidv4(), question: '', answer: '', is_enabled: true, isNew: true }, 
            ...prevFaqs
        ]);
    };

    const handleUpdateFaq = async (id: string, data: Partial<FaqItem>) => {
        const faq = faqs.find(f => f.id === id);
        if (!faq) return;
        const isNew = faq.isNew;
        const payload = { question: faq.question, answer: faq.answer, ...data };

        try {
            if (isNew) {
                await api.post('/api/faqs/', payload);
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

    // Callback to refresh content resources after an update in the child component
    const refreshContentResources = async () => {
        try {
            const data = await api.get('/api/content-resources/');
            setContentResources(data);
        } catch (err) {
            console.error("Failed to refresh content resources", err);
        }
    };

    const renderBusinessDetails = () => {
        if (!profile) return null;
        switch(profile.user_type) {
            case 'realtor':
                return (
                    <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                        <p className="text-base text-slate-300">
                            Your MLS connection is managed automatically, providing the AI with real-time property data.
                        </p>
                    </div>
                );
            case 'therapist':
                return (
                    <ContentDiscovery 
                        initialSpecialties={profile.specialties || []}
                        onSpecialtiesChange={(newSpecialties) => {
                            setProfile(p => p ? { ...p, specialties: newSpecialties } : null)
                        }}
                    />
                );
            default:
                return (
                    <div className="p-4 rounded-lg bg-slate-700/30 border border-slate-600/30">
                        <p className="text-base text-slate-400">No business-specific settings available.</p>
                    </div>
                );
        }
    };
    
    if (isLoading || isContextLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-900">
                <div className="flex items-center gap-4 text-teal-400">
                    <Loader2 className="animate-spin h-8 w-8" />
                    <span className="text-xl">Loading your profile...</span>
                </div>
            </div>
        );
    }

    if (error && !profile) {
        return (
            <div className="p-8 text-center text-red-400 bg-slate-900 h-screen flex items-center justify-center">
                <Card className="p-8">
                    <div className="text-xl">{error}</div>
                </Card>
            </div>
        );
    }

    if (!profile) return null;

    return (
        <>
            {showConfetti && (
                <Confetti
                    width={windowSize.width} 
                    height={windowSize.height} 
                    recycle={false} 
                    numberOfPieces={600}
                    tweenDuration={7000} 
                    colors={[ACTIVE_THEME.primary.from, ACTIVE_THEME.primary.to, ACTIVE_THEME.accent, ACTIVE_THEME.action, '#ffffff']}
                />
            )}

            {/* CORRECTED: Background color to match your app */}
            <div className="h-screen overflow-y-auto bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
                <div className="text-white">
                    <div className="container mx-auto px-6 py-8 max-w-6xl">
                        
                        <header className="mb-12">
                            <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-6">
                                <div className="space-y-3">
                                   <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                                       Profile & Settings
                                   </h1>
                                   <p className="text-xl text-slate-300 leading-relaxed max-w-3xl">
                                       Manage your personal information, configure your AI assistant, and customize your business settings.
                                   </p>
                                </div>
                                <button 
                                    onClick={logout} 
                                    className="px-6 py-3 text-sm font-medium flex items-center gap-3 bg-slate-800/50 hover:bg-slate-700/70 rounded-xl border border-slate-700/50 transition-all duration-200 hover:shadow-lg"
                                >
                                   <LogOut size={18}/> Sign Out
                                </button>
                            </div>
                        </header>

                        {/* Account Information */}
                        <MajorSection
                            icon={<User size={28} />}
                            title="Account Information"
                            description="Manage your personal details, contact information, and account preferences."
                        >
                            <div className="flex justify-between items-start mb-8">
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-1">Personal Details</h3>
                                    <p className="text-slate-400">Update your profile information and preferences.</p>
                                </div>
                                <button 
                                    onClick={() => isEditingProfile ? handleProfileSave() : setIsEditingProfile(true)} 
                                    disabled={isSaving} 
                                    className="px-5 py-2.5 text-sm font-medium flex items-center gap-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            Saving...
                                        </>
                                    ) : isEditingProfile ? (
                                        <>
                                            <Save size={16}/>
                                            Save Changes
                                        </>
                                    ) : (
                                        <>
                                            <Edit3 size={16}/>
                                            Edit Profile
                                        </>
                                    )}
                                </button>
                            </div>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Full Name</label>
                                    <input 
                                        name="full_name" 
                                        value={profile.full_name || ''} 
                                        onChange={handleProfileChange} 
                                        disabled={!isEditingProfile} 
                                        className={`${baseInputStyles} ${!isEditingProfile ? 'opacity-70 cursor-not-allowed' : ''}`} 
                                    />
                                </div>
                                
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Email Address</label>
                                    <input 
                                        name="email" 
                                        type="email" 
                                        value={profile.email || ''} 
                                        onChange={handleProfileChange} 
                                        disabled={!isEditingProfile} 
                                        className={`${baseInputStyles} ${!isEditingProfile ? 'opacity-70 cursor-not-allowed' : ''}`} 
                                    />
                                </div>
                                
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Phone Number</label>
                                    <input 
                                        value={profile.phone_number || 'Not provided'} 
                                        disabled={true} 
                                        className="w-full bg-slate-800/30 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-500 cursor-not-allowed text-base" 
                                    />
                                    <p className="text-xs text-slate-500">Contact support to update your phone number</p>
                                </div>
                                
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Time Zone</label>
                                    <TimezoneSelector 
                                        value={profile.timezone || ''} 
                                        onChange={handleProfileChange} 
                                        disabled={!isEditingProfile} 
                                    />
                                </div>
                                
                                <div className="space-y-2 lg:col-span-2">
                                    <label className="text-sm font-medium text-slate-300">AI Assistant Phone Number</label>
                                    <input 
                                        value={profile.twilio_phone_number || 'Not assigned'} 
                                        disabled={true} 
                                        className="w-full bg-slate-800/30 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-500 cursor-not-allowed text-base" 
                                    />
                                    <p className="text-xs text-slate-500">This number is automatically assigned for your AI assistant</p>
                                </div>
                            </div>
                        </MajorSection>

                        {/* Client Organization */}
                        <MajorSection
                            icon={<Users size={28} />}
                            title="Client Organization"
                            description="Define and manage the roles available for categorizing and organizing your clients."
                        >
                            <RoleManager />
                        </MajorSection>

                        {/* AI Assistant Configuration */}
                        <MajorSection
                            icon={<Bot size={28} />}
                            title="AI Assistant Configuration"
                            description="Set up and train your 24/7 AI assistant to handle client communications using your business knowledge and expertise."
                        >
                            <div className="space-y-10">
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-4">AI AutoPilot Status</h3>
                                    <ToggleSwitch
                                        id="master-ai-toggle"
                                        checked={profile.faq_auto_responder_enabled || false}
                                        onChange={handleMasterSwitchToggle}
                                        label="Enable AI AutoPilot"
                                        description="Allow your AI assistant to automatically respond to client messages using your configured knowledge base and business information."
                                    />
                                </div>

                                <SubSection
                                    icon={<Briefcase size={20} />}
                                    title="Business Context"
                                    description="Provide industry-specific information to help your AI assistant understand your business and better serve your clients."
                                    className="border-t border-slate-700/30 pt-8"
                                >
                                    {renderBusinessDetails()}
                                </SubSection>

                                <SubSection
                                    icon={<Sparkles size={20} />}
                                    title="Knowledge Base (FAQs)"
                                    description="Train your AI by adding frequently asked questions and their answers. The more you add, the smarter your assistant becomes."
                                    action={
                                        <button 
                                            onClick={handleAddFaq} 
                                            className="px-4 py-2 text-sm font-medium flex items-center gap-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg transition-colors"
                                        >
                                            <Plus size={16} /> Add FAQ
                                        </button>
                                    }
                                    className="border-t border-slate-700/30 pt-8 mt-8"
                                >
                                    {faqs.length === 0 ? (
                                        <Card className="p-8 text-center">
                                            <div className="space-y-6">
                                                <div className="w-20 h-20 mx-auto bg-slate-700/50 rounded-full flex items-center justify-center">
                                                    <Sparkles className="w-10 h-10 text-slate-500" />
                                                </div>
                                                <div>
                                                    <h3 className="text-xl font-semibold text-white mb-3">No FAQs Created Yet</h3>
                                                    <p className="text-base text-slate-400 mb-6 max-w-md mx-auto">
                                                        Start building your AI's knowledge by adding frequently asked questions and their responses.
                                                    </p>
                                                    <button 
                                                        onClick={handleAddFaq} 
                                                        className="px-6 py-3 text-sm font-medium flex items-center gap-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg transition-colors mx-auto"
                                                    >
                                                        <Plus size={16} /> Create Your First FAQ
                                                    </button>
                                                </div>
                                            </div>
                                        </Card>
                                    ) : (
                                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
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
                                    )}
                                </SubSection>
                            </div>
                        </MajorSection>

                        {/* Content & Resources */}
                        <MajorSection
                            icon={<Library size={28} />}
                            title="Content & Resources"
                            description="Manage documents, links, and other resources that your AI assistant can share with clients when relevant to their needs."
                        >
                            <ContentResourceManager 
                                api={api} 
                                userRoles={clientRoles} 
                                allResources={contentResources} 
                                onResourcesUpdate={refreshContentResources} 
                            />
                        </MajorSection>

                        {/* Customization & Preferences */}
                        <MajorSection
                            icon={<Settings size={28} />}
                            title="Customization & Preferences"
                            description="Personalize your dashboard experience and manage system preferences to suit your workflow."
                        >
                            <div className="mb-8">
                                <SubSection
                                    icon={<Palette size={20} />}
                                    title="Visual Theme"
                                    description="Choose your preferred color scheme and visual style for the dashboard interface."
                                >
                                    <ThemeSwitcher />
                                </SubSection>
                            </div>
                        </MajorSection>
                    </div>
                </div>
            </div>
        </>
    );
}
