// frontend/components/conversation/ClientIntelCard.tsx
// --- FINAL VERSION: Includes Manual Survey Override Dropdown ---

'use client';

import { useState, useEffect, useMemo, FC } from 'react';
import { Info, Sparkles, Edit, Save, Loader2, Send, AlertTriangle, ChevronDown, ChevronUp, CheckCircle, Eye, X } from 'lucide-react';
import { useAppContext, Client, User } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { ClientIntakeSurvey } from '../survey/ClientIntakeSurvey';

interface QuestionAnswerPair {
    question: string;
    answer: any;
}
interface SurveySubmission {
    id: string;
    completed_at: string;
    survey_title: string;
    questions_and_answers: QuestionAnswerPair[];
}

const PreferenceField: FC<{ label: string; value: any; isEditing?: boolean; onChange?: (value: any) => void; type?: 'text' | 'number' | 'textarea' }> = ({ label, value, isEditing, onChange, type = 'text' }) => {
    const formatValue = (val: any): string => {
        if (val === null || val === undefined || val === '' || (Array.isArray(val) && val.length === 0)) return 'Not set';
        if (typeof val === 'number' && val > 1000 && !label.toLowerCase().includes('year')) {
            return `$${val.toLocaleString()}`;
        }
        if (Array.isArray(val)) return val.join(', ');
        return String(val);
    };

    if (isEditing) {
        return (
            <div>
                <label className="text-xs font-semibold text-gray-400 mb-1 block">{label}</label>
                <input
                    type={type === 'number' ? 'number' : 'text'}
                    value={value || ''}
                    onChange={(e) => onChange?.(e.target.value)}
                    className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm"
                />
            </div>
        );
    }

    return (
        <div className="text-sm">
            <dt className="text-xs text-brand-text-muted flex items-center gap-1.5">{label}</dt>
            <dd className="font-medium text-brand-text-main">{formatValue(value)}</dd>
        </div>
    );
};

const SubmissionModal: FC<{ submission: SurveySubmission | null; onClose: () => void; }> = ({ submission, onClose }) => {
    if (!submission) return null;

    const formatAnswer = (answer: any) => {
        if (answer === null || answer === undefined || answer === '') return <span className="italic text-gray-500">No answer</span>;
        if (Array.isArray(answer)) return answer.join(', ');
        if (typeof answer === 'boolean') return answer ? 'Yes' : 'No';
        return String(answer);
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="w-full max-w-2xl bg-gray-800 border border-white/10 rounded-lg shadow-xl p-6" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h3 className="text-lg font-bold text-white">{submission.survey_title}</h3>
                        <p className="text-xs text-gray-400">Submitted on {new Date(submission.completed_at).toLocaleString()}</p>
                    </div>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-white/10 text-gray-400"><X size={20} /></button>
                </div>
                <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                    {submission.questions_and_answers.map((qa, index) => (
                        <div key={index} className="text-sm">
                            <p className="font-semibold text-gray-300 mb-1">{qa.question}</p>
                            <p className="text-white pl-4 border-l-2 border-cyan-500/30">{formatAnswer(qa.answer)}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};


export const ClientIntelCard = ({ client, onUpdate }: { client: Client | undefined; onUpdate: (updatedClient: Client) => void; }) => {
    const { api, user } = useAppContext();
    const [isEditing, setIsEditing] = useState(false);
    const [editablePrefs, setEditablePrefs] = useState<Client['preferences']>({});
    const [isSaving, setIsSaving] = useState(false);
    const [showSurvey, setShowSurvey] = useState(false);
    const [sendingSurvey, setSendingSurvey] = useState(false);
    const [showRawData, setShowRawData] = useState(false);
    const [showSubmissionModal, setShowSubmissionModal] = useState(false);
    const [submissionData, setSubmissionData] = useState<SurveySubmission | null>(null);
    const [isLoadingSubmission, setIsLoadingSubmission] = useState(false);
    const [availableSurveys, setAvailableSurveys] = useState<{name: string, type: string}[]>([]);
    const [overrideSurveyType, setOverrideSurveyType] = useState<string>('');

    const intel = useMemo(() => {
        if (!client) return { summary: null, actions: [], canonicalPrefs: {}, rawPrefs: {} };
        let summary: string | null = null;
        let actions: string[] = [];
        const notes = client.notes || '';
        const summaryMatch = notes.match(/AI Summary \(.*\):\n([\s\S]*?)\n\n/);
        if (summaryMatch) summary = summaryMatch[1];
        const actionsMatch = notes.match(/Actionable Intel: (.*)/);
        if (actionsMatch) actions = actionsMatch[1].split(', ');
        const canonicalKeys = new Set([
            "objective", "budget_max", "preapproval_status", "min_bedrooms", "max_bedrooms",
            "min_bathrooms", "max_bathrooms", "min_sqft", "min_acreage", "max_hoa_fee",
            "min_year_built", "property_types", "locations", "must_haves", "deal_breakers",
            "timeline", "urgency_level", "property_address", "property_type", "bedrooms",
            "bathrooms", "sqft", "acreage", "year_built", "property_condition",
            "features_and_upgrades", "desired_sale_price", "bottom_line_price",
            "timeline_to_sell", "ideal_closing_date", "motivation_for_selling",
            "is_occupied", "remaining_mortgage", "primary_concerns", "therapy_experience",
            "client_goals", "preferred_approaches", "session_frequency"
        ]);
        const canonicalPrefs: Client['preferences'] = {};
        const rawPrefs: Client['preferences'] = {};
        for (const [key, value] of Object.entries(client.preferences || {})) {
            if (canonicalKeys.has(key)) canonicalPrefs[key] = value;
            else rawPrefs[key] = value;
        }
        return { summary, actions, canonicalPrefs, rawPrefs };
    }, [client]);

    useEffect(() => {
        if (client) setEditablePrefs(intel.canonicalPrefs || {});
    }, [client, intel.canonicalPrefs]);

    useEffect(() => {
        const fetchAvailableSurveys = async () => {
            if (!user) return;
            try {
                const data = await api.get('/api/surveys/available');
                const surveyTypes = data.survey_types.map((type: string) => ({
                    name: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    type: type
                }));
                setAvailableSurveys(surveyTypes);
                if (surveyTypes.length > 0 && !overrideSurveyType) {
                    setOverrideSurveyType(surveyTypes[0].type);
                }
            } catch (error) {
                console.error("Failed to fetch available surveys:", error);
            }
        };
        fetchAvailableSurveys();
    }, [user, api, overrideSurveyType]);

    if (!client) return null;

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const payload = { preferences: editablePrefs };
            const updatedClient = await api.put(`/api/clients/${client.id}`, payload);
            onUpdate(updatedClient);
            setIsEditing(false);
        } catch(err) {
            console.error("Failed to save client intel:", err);
            alert("Failed to save intel.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setIsEditing(false);
        setEditablePrefs(intel.canonicalPrefs || {});
    };

    const handleSurveyComplete = () => {
        setShowSurvey(false);
        onUpdate(client);
    };

    const handleSendSurvey = async () => {
        if (!client || !client.phone) return;
        setSendingSurvey(true);
        try {
            const payload = {
                survey_type: overrideSurveyType || undefined,
            };
            await api.post(`/api/surveys/send/${client.id}`, payload);
            onUpdate({ ...client, intake_survey_sent_at: new Date().toISOString() });
        } catch (error) {
            console.error('Failed to send survey:', error);
            alert('Failed to send survey. Please try again.');
        } finally {
            setSendingSurvey(false);
        }
    };

    const handleViewSubmission = async () => {
        if (!client) return;
        setIsLoadingSubmission(true);
        try {
            const submissions: SurveySubmission[] = await api.get(`/api/surveys/client/${client.id}`);
            if (submissions && submissions.length > 0) {
                setSubmissionData(submissions[0]);
                setShowSubmissionModal(true);
            } else {
                alert("No completed survey submissions found for this client.");
            }
        } catch (error) {
            console.error("Failed to fetch survey submission:", error);
            alert("Could not load survey submission.");
        } finally {
            setIsLoadingSubmission(false);
        }
    };
    
    const renderThematicGroups = () => {
        if (!user) return null;
        const isSeller = client.user_tags?.includes('seller') || client.ai_tags?.includes('seller');
        switch (user.vertical) {
            case 'therapy':
                return (
                    <div className="space-y-4 pt-4 border-t border-white/10">
                        <div>
                            <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Client Focus</h4>
                            <div className="grid grid-cols-1 gap-x-4 gap-y-3">
                                <PreferenceField label="Primary Concerns" value={intel.canonicalPrefs.primary_concerns} />
                                <PreferenceField label="Client Goals" value={intel.canonicalPrefs.client_goals} />
                            </div>
                        </div>
                        <div>
                            <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Session Preferences</h4>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                <PreferenceField label="Session Frequency" value={intel.canonicalPrefs.session_frequency} />
                                <PreferenceField label="Preferred Approaches" value={intel.canonicalPrefs.preferred_approaches} />
                                <PreferenceField label="Therapy Experience" value={intel.canonicalPrefs.therapy_experience} />
                            </div>
                        </div>
                    </div>
                );
            case 'real_estate':
                if (isSeller) {
                    return (
                        <div className="space-y-4 pt-4 border-t border-white/10">
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Property Details</h4>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                    <PreferenceField label="Address" value={intel.canonicalPrefs.property_address} />
                                    <PreferenceField label="Property Type" value={intel.canonicalPrefs.property_type} />
                                    <PreferenceField label="Bedrooms" value={intel.canonicalPrefs.bedrooms} />
                                    <PreferenceField label="Bathrooms" value={intel.canonicalPrefs.bathrooms} />
                                </div>
                            </div>
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Sale Objectives</h4>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                    <PreferenceField label="Desired Price" value={intel.canonicalPrefs.desired_sale_price} />
                                    <PreferenceField label="Timeline" value={intel.canonicalPrefs.timeline_to_sell} />
                                </div>
                            </div>
                        </div>
                    );
                } else {
                    return (
                        <div className="space-y-4 pt-4 border-t border-white/10">
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Budget & Financials</h4>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                    <PreferenceField label="Max Budget" value={intel.canonicalPrefs.budget_max} />
                                    <PreferenceField label="Pre-Approved" value={intel.canonicalPrefs.preapproval_status} />
                                </div>
                            </div>
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Property Requirements</h4>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                    <PreferenceField label="Min Bedrooms" value={intel.canonicalPrefs.min_bedrooms} />
                                    <PreferenceField label="Min Bathrooms" value={intel.canonicalPrefs.min_bathrooms} />
                                    <PreferenceField label="Locations" value={intel.canonicalPrefs.locations} />
                                    <PreferenceField label="Property Types" value={intel.canonicalPrefs.property_types} />
                                </div>
                            </div>
                        </div>
                    );
                }
            default:
                return null;
        }
    };

    return (
        <>
            <InfoCard title="Intelligent Briefing" icon={<Info size={14} />} onEdit={!isEditing ? () => setIsEditing(true) : undefined}>
                <div className="pt-2 space-y-4">
                    {intel.actions.length > 0 && intel.actions[0] && (
                        <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-3">
                            <AlertTriangle size={16} className="text-yellow-400 flex-shrink-0" />
                            <p className="text-sm text-yellow-300 font-semibold">{intel.actions.join(', ')}</p>
                        </div>
                    )}
                    {intel.summary && (
                        <div className="flex items-start gap-3 text-sm">
                            <Sparkles size={14} className="flex-shrink-0 mt-0.5 text-brand-accent" />
                            <p className="text-gray-300">{intel.summary}</p>
                        </div>
                    )}
                    
                    {isEditing ? (
                        <div className="space-y-4 pt-4 border-t border-white/10">
                            <div className="grid grid-cols-2 gap-4">
                                {Object.entries(editablePrefs).map(([key, value]) => (
                                    <PreferenceField
                                        key={key}
                                        label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        value={value} isEditing
                                        onChange={(newValue) => setEditablePrefs(p => ({...p, [key]: newValue}))}
                                        type={typeof value === 'number' ? 'number' : 'text'}
                                    />
                                ))}
                            </div>
                            <div className="flex gap-2 justify-end">
                                <button onClick={handleCancel} className="px-3 py-1 text-xs font-semibold bg-white/10 rounded-md">Cancel</button>
                                <button onClick={handleSave} disabled={isSaving} className="px-3 py-1 text-xs font-semibold bg-primary-action text-brand-dark rounded-md flex items-center gap-1.5">
                                   {isSaving ? <Loader2 className="h-4 w-4 animate-spin"/> : <Save size={14}/>} Save Changes
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            {renderThematicGroups()}
                            {Object.keys(intel.rawPrefs).length > 0 && (
                                <div className="pt-2 border-t border-white/10">
                                    <button onClick={() => setShowRawData(!showRawData)} className="w-full flex justify-between items-center text-xs text-gray-400 hover:text-white">
                                        <span>View Raw Data ({Object.keys(intel.rawPrefs).length} items)</span>
                                        {showRawData ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                    </button>
                                    {showRawData && (
                                        <div className="mt-2 p-2 bg-black/20 rounded-md">
                                            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                                {Object.entries(intel.rawPrefs).map(([key, value]) => (
                                                    <PreferenceField key={key} label={key.replace(/_/g, ' ')} value={value} />
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}

                    {!isEditing && (
                        client.intake_survey_completed ? (
                            <div className="mt-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg space-y-3">
                                <div>
                                    <h4 className="text-xs font-bold text-green-400 uppercase flex items-center gap-2"><CheckCircle size={14}/>SURVEY STATUS</h4>
                                    <p className="text-xs text-gray-400 mt-1">Intel gathered from the client's last submission.</p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleViewSubmission}
                                        disabled={isLoadingSubmission}
                                        className="flex-1 flex items-center justify-center gap-1.5 px-2 py-2 bg-white/10 text-white text-xs font-semibold rounded-md hover:bg-white/20 transition-colors disabled:opacity-50"
                                    >
                                        {isLoadingSubmission ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
                                        View Submission
                                    </button>
                                    <div className="flex-1 flex gap-2">
                                        <select 
                                            value={overrideSurveyType} 
                                            onChange={(e) => setOverrideSurveyType(e.target.value)}
                                            className="flex-grow bg-white/5 border border-white/10 rounded-md px-2 text-xs text-white focus:border-cyan-500 focus:ring-0"
                                        >
                                            {availableSurveys.map(s => <option key={s.type} value={s.type}>{s.name}</option>)}
                                        </select>
                                        <button 
                                            onClick={handleSendSurvey}
                                            disabled={sendingSurvey || !client.phone}
                                            title="Resend selected survey"
                                            className="px-3 py-2 bg-cyan-500 text-white rounded-md hover:bg-cyan-600 disabled:opacity-50"
                                        >
                                            {sendingSurvey ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="mt-4 p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg space-y-3">
                                <div>
                                    <h4 className="text-xs font-bold text-cyan-400 uppercase">GATHER INTEL</h4>
                                    <p className="text-xs text-gray-400 mt-1">
                                        {client.intake_survey_sent_at ? `Survey sent on ${new Date(client.intake_survey_sent_at).toLocaleDateString()}.` : 'No survey has been sent yet.'}
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    <div className="flex-1 flex gap-2">
                                        <button onClick={handleSendSurvey} disabled={sendingSurvey || !client.phone} title="Send selected survey" className="flex-grow flex items-center justify-center gap-1.5 px-2 py-2 bg-cyan-500 text-white text-xs font-semibold rounded-md hover:bg-cyan-600 disabled:opacity-50">
                                            {sendingSurvey ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />} Send
                                        </button>
                                        <select 
                                           value={overrideSurveyType} 
                                           onChange={(e) => setOverrideSurveyType(e.target.value)}
                                           className="bg-white/5 border border-white/10 rounded-md px-2 text-xs text-white focus:border-cyan-500 focus:ring-0"
                                        >
                                           {availableSurveys.map(s => <option key={s.type} value={s.type}>{s.name}</option>)}
                                        </select>
                                    </div>
                                    <button onClick={() => setShowSurvey(true)} className="flex-1 px-2 py-2 bg-white/10 text-white text-xs font-semibold rounded-md hover:bg-white/20">
                                        Enter Manually
                                    </button>
                                </div>
                            </div>
                        )
                    )}
                </div>
                
                {showSurvey && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="w-full max-w-2xl">
                            <ClientIntakeSurvey clientId={client.id} onComplete={handleSurveyComplete} onCancel={() => setShowSurvey(false)} />
                        </div>
                    </div>
                )}
            </InfoCard>
            
            {showSubmissionModal && (
                <SubmissionModal 
                    submission={submissionData} 
                    onClose={() => {
                        setShowSubmissionModal(false);
                        setSubmissionData(null);
                    }} 
                />
            )}
        </>
    );
};