// frontend/app/(main)/profile/page.tsx
// --- FINAL FIX: Corrects the case-sensitivity mismatch for question_type ---

"use client";

import { useState, useEffect, ChangeEvent, FC } from "react";
import { Trash2, Edit3, Save, XCircle, Loader2, User, Briefcase, Bot, LogOut, Sparkles, Library, Palette, MessageSquareQuote, ChevronDown, Check } from 'lucide-react';
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

// --- [FIX #1] SURVEY QUESTION ITEM INTERFACE ---
// The question_type must be a lowercase string union to match the backend Enum.
export interface SurveyQuestionItem {
    id: string;
    survey_type: string;
    question_text: string;
    question_type: 'text' | 'number' | 'select' | 'multi_select' | 'boolean';
    options?: string[];
    is_required: boolean;
    placeholder?: string;
    help_text?: string;
    preference_key?: string;
    display_order: number;
    isNew?: boolean;
}

const baseInputStyles = "w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition text-sm";

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
    <div className={`flex flex-col w-full rounded-xl border bg-gray-900/50 p-5 transition-all ${isMasterEnabled && item.is_enabled ? 'border-white/20' : 'border-white/10 bg-gray-900/80'}`}>
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

const SurveyQuestionCard: FC<{
  item: SurveyQuestionItem;
  onUpdate: (id: string, data: Partial<SurveyQuestionItem>) => Promise<void>;
  onRemove: (id: string) => void;
}> = ({ item, onUpdate, onRemove }) => {
    const [isEditing, setIsEditing] = useState(item.isNew || false);
    const [currentQuestion, setCurrentQuestion] = useState(item);

    const handleSave = () => {
        if (currentQuestion.question_text.trim() === '') return;
        onUpdate(item.id, { ...currentQuestion, isNew: false });
        setIsEditing(false);
    };

    const handleCancel = () => {
        if (item.isNew) {
            onRemove(item.id);
        } else {
            setCurrentQuestion(item);
            setIsEditing(false);
        }
    };
    
    const handleInputChange = (field: keyof SurveyQuestionItem, value: any) => {
        setCurrentQuestion(prev => ({...prev, [field]: value}));
    };

    // --- [FIX #2] QUESTION TYPES ARRAY ---
    // This array must contain the lowercase values that the backend expects.
    const questionTypes: SurveyQuestionItem['question_type'][] = ['text', 'number', 'select', 'multi_select', 'boolean'];

    if (isEditing) {
        return (
            <div className="flex flex-col w-full rounded-xl border border-teal-500/50 bg-gray-900/50 p-5 space-y-4">
                <div>
                    <label className="text-xs font-semibold text-gray-400">Question</label>
                    <input value={currentQuestion.question_text} onChange={(e) => handleInputChange('question_text', e.target.value)} placeholder="e.g., What's your maximum budget?" className={`mt-1 ${baseInputStyles}`} />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                     <div>
                        <label className="text-xs font-semibold text-gray-400">Question Type</label>
                        <select value={currentQuestion.question_type} onChange={e => handleInputChange('question_type', e.target.value as SurveyQuestionItem['question_type'])} className={`mt-1 ${baseInputStyles}`}>
                            {questionTypes.map(type => 
                                <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}</option>
                            )}
                        </select>
                    </div>
                    <div className="flex items-end pb-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={currentQuestion.is_required} onChange={e => handleInputChange('is_required', e.target.checked)} className="h-4 w-4 rounded bg-gray-700 border-gray-600 text-teal-500 focus:ring-teal-500" />
                            <span className="text-sm text-gray-300">Required</span>
                        </label>
                    </div>
                </div>

                {(currentQuestion.question_type === 'select' || currentQuestion.question_type === 'multi_select') && (
                    <div>
                        <label className="text-xs font-semibold text-gray-400">Options (one per line)</label>
                        <textarea 
                            value={currentQuestion.options?.join('\n') || ''} 
                            onChange={e => handleInputChange('options', e.target.value ? e.target.value.split('\n') : [])}
                            placeholder="Option 1&#10;Option 2&#10;Option 3"
                            rows={3} className={`mt-1 ${baseInputStyles} resize-none`} 
                        />
                    </div>
                )}
                
                <div className="flex justify-end gap-2 border-t border-white/10 pt-4">
                    <button onClick={handleCancel} className="px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5 text-gray-300 hover:bg-gray-700"><XCircle size={14} /> Cancel</button>
                    <button onClick={handleSave} className="px-3 py-1.5 text-sm rounded-md flex items-center gap-1.5 btn-primary"><Save size={14} /> Save</button>
                </div>
            </div>
        );
    }
    
    return (
        <div className="flex w-full rounded-xl border border-white/20 bg-gray-900/50 p-5 transition-all">
            <div className="flex-grow">
                <div className="flex justify-between items-start">
                    <h3 className="font-semibold text-white mb-2">{currentQuestion.question_text || "New Question"}</h3>
                    <span className="text-xs font-bold text-teal-400 bg-teal-500/10 px-2 py-1 rounded-full uppercase">{currentQuestion.question_type.replace('_', ' ')}</span>
                </div>
                {currentQuestion.is_required && <p className="text-xs text-red-400 mb-2">Required</p>}
                {(currentQuestion.question_type === 'select' || currentQuestion.question_type === 'multi_select') && (
                    <div className="text-sm text-gray-400 space-x-2">
                        <span>Options:</span>
                        {(currentQuestion.options || []).map(opt => <span key={opt} className="bg-white/10 px-1.5 py-0.5 rounded text-xs">{opt}</span>)}
                    </div>
                )}
            </div>
            <div className="flex flex-col justify-center items-center ml-4 pl-4 border-l border-white/10">
                <button onClick={() => onRemove(item.id)} className="p-2 rounded-md text-red-400 hover:bg-red-500/10"><Trash2 size={16} /></button>
                <button onClick={() => setIsEditing(true)} className="p-2 rounded-md text-blue-400 hover:bg-blue-500/10"><Edit3 size={16} /></button>
            </div>
        </div>
    );
};

const SurveyQuestionManager = () => {
    const { api } = useAppContext();
    const [availableSurveys, setAvailableSurveys] = useState<{name: string, type: string}[]>([]);
    const [selectedSurvey, setSelectedSurvey] = useState<string>('');
    const [questions, setQuestions] = useState<SurveyQuestionItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAvailable = async () => {
            try {
                const data = await api.get('/api/surveys/available');
                const surveyTypes = data.survey_types.map((type: string) => ({
                    name: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    type: type
                }));
                setAvailableSurveys(surveyTypes);
                if (surveyTypes.length > 0) {
                    setSelectedSurvey(surveyTypes[0].type);
                }
            } catch (err) {
                setError('Failed to load available surveys.');
            }
        };
        fetchAvailable();
    }, [api]);
    
    useEffect(() => {
        if (!selectedSurvey) return;
        const fetchAndInitializeQuestions = async () => {
            setIsLoading(true);
            setError(null);
            try {
                // Step 1: Check if the user ALREADY has custom questions.
                let customQuestions = await api.get(`/api/surveys/custom-questions/${selectedSurvey}`);

                // Step 2: If they have NO custom questions, this is their first time editing.
                if (customQuestions.length === 0) {
                    // Fetch the system defaults to use as a template.
                    const defaultConfig = await api.get(`/api/surveys/config/${selectedSurvey}`);
                    const defaultQuestions = defaultConfig.questions;

                    // Create a personal, editable copy of each default question in the database.
                    const creationPromises = defaultQuestions.map((q: any, index: number) => {
                        const payload = {
                            survey_type: selectedSurvey,
                            question_text: q.question,
                            question_type: q.type,
                            options: q.options,
                            is_required: q.required,
                            placeholder: q.placeholder,
                            help_text: q.help_text,
                            preference_key: q.preference_key,
                            display_order: index,
                        };
                        return api.post('/api/surveys/custom-questions', payload);
                    });
                    
                    // Wait for all questions to be created.
                    await Promise.all(creationPromises);

                    // Now, refetch the newly created custom questions.
                    customQuestions = await api.get(`/api/surveys/custom-questions/${selectedSurvey}`);
                }

                // Step 3: Set the questions in the state. From now on, the user is only editing their own copies.
                setQuestions(customQuestions);

            } catch (err) {
                setError(`Failed to load questions for ${selectedSurvey}.`);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAndInitializeQuestions();
    }, [selectedSurvey, api]);
    
    const handleAddQuestion = () => {
        const newQuestion: SurveyQuestionItem = {
            id: uuidv4(),
            survey_type: selectedSurvey,
            question_text: '',
            // --- [FIX #3] ADD QUESTION DEFAULT ---
            // The default type for a new question must also be lowercase.
            question_type: 'text',
            is_required: false,
            display_order: questions.length,
            isNew: true,
        };
        setQuestions(prev => [newQuestion, ...prev]);
    };

    const handleUpdateQuestion = async (id: string, data: Partial<SurveyQuestionItem>) => {
        const question = questions.find(q => q.id === id);
        if (!question) return;
        
        try {
            if (question.isNew) {
                const payload = {
                    survey_type: data.survey_type,
                    question_text: data.question_text,
                    question_type: data.question_type,
                    options: data.options,
                    is_required: data.is_required,
                    placeholder: data.placeholder,
                    help_text: data.help_text,
                    preference_key: data.preference_key,
                    display_order: data.display_order,
                };
                await api.post('/api/surveys/custom-questions', payload);
            } else {
                await api.put(`/api/surveys/custom-questions/${id}`, data);
            }
            const refreshedData = await api.get(`/api/surveys/custom-questions/${selectedSurvey}`);
            setQuestions(refreshedData);
        } catch (err) {
            setError("Failed to save question.");
        }
    };
    
    const handleRemoveQuestion = async (id: string) => {
        const isNew = questions.find(f => f.id === id)?.isNew;
        if (isNew) {
            setQuestions(questions.filter(f => f.id !== id));
            return;
        }
        try {
            await api.del(`/api/surveys/custom-questions/${id}`);
            setQuestions(questions.filter(f => f.id !== id));
        } catch (err) {
            setError("Failed to remove question.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-3"><MessageSquareQuote /> Client Intake Surveys</h3>
                    <p className="text-sm text-gray-400 mt-1">Customize the questions you ask new clients to tailor their experience.</p>
                </div>
                <button onClick={handleAddQuestion} disabled={!selectedSurvey || isLoading} className="btn-secondary px-3 py-1.5 text-sm font-semibold flex items-center gap-2 whitespace-nowrap disabled:opacity-50">+ Add Question</button>
            </div>

            {availableSurveys.length > 0 && (
                 <div>
                    <label htmlFor="survey-selector" className="text-sm font-medium text-gray-400">Editing Survey For:</label>
                    <select id="survey-selector" value={selectedSurvey} onChange={e => setSelectedSurvey(e.target.value)} className={`mt-1 w-full md:w-1/2 ${baseInputStyles}`}>
                        {availableSurveys.map(s => <option key={s.type} value={s.type}>{s.name}</option>)}
                    </select>
                </div>
            )}
            
            {isLoading ? (
                <div className="flex justify-center items-center py-8"><Loader2 className="animate-spin h-6 w-6 text-teal-400" /></div>
            ) : error ? (
                <div className="text-center py-8 text-red-400">{error}</div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {questions.map(q => <SurveyQuestionCard key={q.id} item={q} onUpdate={handleUpdateQuestion} onRemove={handleRemoveQuestion} />)}
                </div>
            )}
        </div>
    );
};

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
    }, [user, handleProfileSave]);

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

    const renderBusinessDetails = () => {
        if (!profile) return null;
        switch(profile.user_type) {
            case 'realtor':
                return <p className="text-sm text-gray-400">Your MLS connection is managed automatically, providing the AI with real-time property data.</p>;
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
                return <p className="text-sm text-gray-500">No business-specific settings available.</p>;
        }
    };
    
    if (isLoading || isContextLoading) return <div className="flex items-center justify-center h-screen bg-gray-900"><Loader2 className="animate-spin h-8 w-8 text-teal-500" /></div>;
    if (error && !profile) return <div className="p-8 text-center text-red-400 bg-gray-900">{error}</div>;
    if (!profile) return null;

    return (
        <>
            {showConfetti && (
                <Confetti
                    width={windowSize.width} height={windowSize.height} recycle={false} numberOfPieces={600}
                    tweenDuration={7000} colors={[ACTIVE_THEME.primary.from, ACTIVE_THEME.primary.to, ACTIVE_THEME.accent, ACTIVE_THEME.action, '#ffffff']}
                />
            )}

            <main className="flex-1 overflow-y-auto bg-gray-900 text-white p-6 md:p-8 lg:p-12">
                <div className="max-w-5xl mx-auto space-y-12">

                    <div className="flex justify-between items-start">
                        <div>
                           <h1 className="text-3xl font-bold text-white">Profile & Settings</h1>
                           <p className="text-gray-400 mt-1">Manage your account details, AI assistant, and content.</p>
                        </div>
                        <button onClick={logout} className="px-4 py-2 text-sm font-semibold flex items-center gap-2 bg-gray-700/50 hover:bg-gray-700 rounded-md">
                           <LogOut size={16}/> Logout
                        </button>
                    </div>

                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <div className="flex justify-between items-center mb-6">
                            <div className="flex items-center gap-3">
                                <User className="w-6 h-6 text-gray-300"/>
                                <h2 className="text-xl font-bold text-white">My Profile</h2>
                            </div>
                             <button onClick={() => isEditingProfile ? handleProfileSave() : setIsEditingProfile(true)} disabled={isSaving} className="btn-primary px-4 py-2 text-sm font-semibold flex items-center gap-2">
                                 {isSaving ? <><Loader2 className="h-4 w-4 animate-spin" />Saving...</> : (isEditingProfile ? <><Save size={16}/>Save Profile</> : <><Edit3 size={16}/>Edit Profile</>)}
                             </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-1"><label className="text-sm font-medium text-gray-400">Full Name</label><input name="full_name" value={profile.full_name || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50" /></div>
                            <div className="space-y-1"><label className="text-sm font-medium text-gray-400">Your Personal Phone</label><input value={profile.phone_number || ''} disabled={true} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed" /></div>
                            <div className="space-y-1"><label className="text-sm font-medium text-gray-400">Email Address</label><input name="email" type="email" value={profile.email || ''} onChange={handleProfileChange} disabled={!isEditingProfile} className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50" /></div>
                            <div className="space-y-1"><label className="text-sm font-medium text-gray-400">My Default Time Zone</label><TimezoneSelector value={profile.timezone || ''} onChange={handleProfileChange} disabled={!isEditingProfile} /></div>
                            <div className="space-y-1"><label className="text-sm font-medium text-gray-400">AI Nudge Number</label><input value={profile.twilio_phone_number || 'Not assigned'} disabled={true} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed" /></div>
                        </div>
                    </div>

                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8 space-y-8">
                        <div>
                            <div className="flex items-center gap-3">
                                <Bot className="w-6 h-6 text-cyan-400" />
                                <h2 className="text-xl font-bold text-white">AI Nudge AutoPilot</h2>
                            </div>
                            <p className="text-gray-300 mt-2">
                                Your business's own ChatGPT, answering client texts 24/7. Train it with your unique knowledge.
                            </p>
                        </div>
                        
                        <div className="flex items-center space-x-3 p-4 rounded-lg bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20">
                            <input type="checkbox" id="master-faq-toggle" checked={profile.faq_auto_responder_enabled} onChange={(e) => handleMasterSwitchToggle(e.target.checked)} className="h-4 w-4 rounded bg-white/10 border-white/20 text-cyan-500 focus:ring-cyan-500" />
                            <label htmlFor="master-faq-toggle" className="text-base font-medium text-white">Enable AutoPilot</label>
                        </div>
                        
                        <div className="border-t border-white/10 pt-6">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-3"><Briefcase /> Business Context</h3>
                            <p className="text-sm text-gray-400 mt-1 mb-4">Provide key details about your business for the AI to use in conversation.</p>
                            {renderBusinessDetails()}
                        </div>

                        <div className="border-t border-white/10 pt-6">
                            <SurveyQuestionManager />
                        </div>
                        
                        <div className="border-t border-white/10 pt-6">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <h3 className="text-lg font-semibold text-white flex items-center gap-3"><Sparkles /> Knowledge Base (FAQs)</h3>
                                    <p className="text-sm text-gray-400 mt-1">Train your AI by adding question-and-answer pairs. The more you add, the smarter it gets.</p>
                                </div>
                                <button onClick={handleAddFaq} className="btn-secondary px-3 py-1.5 text-sm font-semibold flex items-center gap-2 whitespace-nowrap">+ Add FAQ</button>
                            </div>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {faqs.map(faq => (
                                    <FaqCard key={faq.id} item={faq} onUpdate={handleUpdateFaq} onRemove={handleRemoveFaq} isMasterEnabled={profile.faq_auto_responder_enabled || false} />
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <div className="flex items-center gap-3">
                           <Library className="w-6 h-6 text-teal-300"/>
                           <h2 className="text-xl font-bold text-white">Content Resource Library</h2>
                        </div>
                        <p className="text-gray-300 mt-2 mb-6">Upload documents and links that your AI assistant can intelligently share with clients when relevant.</p>
                        <ContentResourceManager api={api} />
                    </div>
                    
                    <div className="bg-gray-800/40 rounded-xl border border-white/10 p-8">
                        <div className="flex items-center gap-3">
                           <Palette className="w-6 h-6 text-purple-300"/>
                           <h2 className="text-xl font-bold text-white">App Appearance</h2>
                        </div>
                        <p className="text-gray-300 mt-2 mb-6">Choose your preferred color scheme for the dashboard.</p>
                        <ThemeSwitcher />
                    </div>

                </div>
            </main>
        </>
    );
}