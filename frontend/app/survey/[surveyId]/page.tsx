// app/survey/[surveyId]/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, ArrowRight, ArrowLeft, Loader2, Send, AlertCircle, User, Mail } from 'lucide-react';
import { Avatar } from '@/components/ui/Avatar';

interface SurveyQuestion {
    id: string;
    type: 'text' | 'number' | 'select' | 'multi_select' | 'range' | 'boolean';
    question: string;
    required: boolean;
    options?: string[];
    placeholder?: string;
    help_text?: string;
}

interface SurveyConfig {
    survey_type: string;
    title: string;
    description: string;
    estimated_time: string;
    questions: SurveyQuestion[];
}

interface SurveyInfo {
    survey_id: string;
    client_name: string;
    user_name: string;
    user_avatar_url?: string; // Add professional's avatar URL
    user_email?: string; // Add professional's email
    survey_type: string;
}

export default function PublicSurveyPage() {
    const params = useParams();
    const surveyId = params.surveyId as string;

    const [surveyInfo, setSurveyInfo] = useState<SurveyInfo | null>(null);
    const [surveyConfig, setSurveyConfig] = useState<SurveyConfig | null>(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [responses, setResponses] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [completed, setCompleted] = useState(false);

    // (Data fetching and state logic remains the same)
    useEffect(() => {
        const loadSurvey = async () => {
            setLoading(true);
            setError(null);
            try {
                const infoResponse = await fetch(`http://localhost:8001/api/surveys/public/info/${surveyId}`);
                if (!infoResponse.ok) {
                    const errorData = await infoResponse.json();
                    throw new Error(errorData.detail || 'Survey not found or expired');
                }
                const info = await infoResponse.json();
                setSurveyInfo(info);

                const configResponse = await fetch(`http://localhost:8001/api/surveys/public/config/${info.template_id}?survey_id=${surveyId}`);
                if (!configResponse.ok) {
                    const errorData = await configResponse.json();
                    throw new Error(errorData.detail || 'Survey configuration not found');
                }
                const config = await configResponse.json();
                setSurveyConfig(config);
            } catch (err: any) {
                setError(err.message || 'Failed to load survey');
            } finally {
                setLoading(false);
            }
        };
        if (surveyId) {
            loadSurvey();
        }
    }, [surveyId]);

    const handleResponseChange = (questionId: string, value: any) => {
        setResponses(prev => ({ ...prev, [questionId]: value }));
    };

    const handleMultiSelectChange = (questionId: string, option: string) => {
        setResponses(prev => {
            const currentValues = prev[questionId] || [];
            const newValues = currentValues.includes(option)
                ? currentValues.filter((v: string) => v !== option)
                : [...currentValues, option];
            return { ...prev, [questionId]: newValues };
        });
    };

    const isStepValid = () => {
        if (!surveyConfig) return false;
        const currentQuestion = surveyConfig.questions[currentStep];
        if (!currentQuestion.required) return true;

        const response = responses[currentQuestion.id];
        if (currentQuestion.type === 'multi_select') {
            return response && response.length > 0;
        }
        return response !== undefined && response !== null && response !== '';
    };

    const canGoNext = () => {
        return isStepValid() && currentStep < (surveyConfig?.questions.length || 0) - 1;
    };

    const canSubmit = () => {
        if (!surveyConfig) return false;
        for (const question of surveyConfig.questions) {
            if (question.required) {
                const response = responses[question.id];
                if (question.type === 'multi_select') {
                    if (!response || response.length === 0) return false;
                } else {
                    if (response === undefined || response === null || response === '') return false;
                }
            }
        }
        return true;
    };

    const handleNext = () => {
        if (canGoNext()) {
            setCurrentStep(prev => prev + 1);
        }
    };

    const handlePrevious = () => {
        if (currentStep > 0) {
            setCurrentStep(prev => prev - 1);
        }
    };

    const handleSubmit = async () => {
        if (!canSubmit()) return;
        setSubmitting(true);
        setError(null);
        try {
            const response = await fetch(`http://localhost:8001/api/surveys/public/response/${surveyId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(responses),
            });
            if (!response.ok) {
                throw new Error('Failed to submit survey');
            }
            setCompleted(true);
        } catch (err: any) {
            setError(err.message || 'Failed to submit survey');
        } finally {
            setSubmitting(false);
        }
    };

    const renderQuestion = (question: SurveyQuestion) => {
        const response = responses[question.id];
        const baseInputClasses = "w-full bg-slate-50 border-2 border-slate-200 rounded-lg px-4 py-3 text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-none transition-colors duration-200";

        switch (question.type) {
            case 'text':
                return <input type="text" value={response || ''} onChange={(e) => handleResponseChange(question.id, e.target.value)} placeholder={question.placeholder} className={baseInputClasses} />;
            case 'number':
                return <input type="number" value={response || ''} onChange={(e) => handleResponseChange(question.id, e.target.value)} placeholder={question.placeholder} className={baseInputClasses} />;
            case 'select':
                return (
                    <select value={response || ''} onChange={(e) => handleResponseChange(question.id, e.target.value)} className={baseInputClasses}>
                        <option value="">Select an option...</option>
                        {question.options?.map((option) => (<option key={option} value={option}>{option}</option>))}
                    </select>
                );
            case 'multi_select':
                return (
                    <div className="space-y-3">
                        {question.options?.map((option) => (
                            <label key={option} className="flex items-center gap-3 p-4 bg-slate-50 hover:bg-blue-50 border-2 border-slate-200 hover:border-blue-400 rounded-lg cursor-pointer transition-colors duration-200">
                                <input type="checkbox" checked={response?.includes(option) || false} onChange={() => handleMultiSelectChange(question.id, option)} className="w-5 h-5 text-blue-600 border-slate-300 rounded focus:ring-blue-500" />
                                <span className="text-slate-700 font-medium select-none">{option}</span>
                            </label>
                        ))}
                    </div>
                );
            case 'boolean':
                return (
                    <div className="flex flex-col sm:flex-row gap-3">
                        <label className="flex-1 flex items-center gap-3 p-4 bg-slate-50 hover:bg-blue-50 border-2 border-slate-200 hover:border-blue-400 rounded-lg cursor-pointer transition-colors duration-200">
                            <input type="radio" name={question.id} value="true" checked={response === true} onChange={() => handleResponseChange(question.id, true)} className="w-5 h-5 text-blue-600 border-slate-300 focus:ring-blue-500" />
                            <span className="text-slate-700 font-medium select-none">Yes</span>
                        </label>
                        <label className="flex-1 flex items-center gap-3 p-4 bg-slate-50 hover:bg-blue-50 border-2 border-slate-200 hover:border-blue-400 rounded-lg cursor-pointer transition-colors duration-200">
                            <input type="radio" name={question.id} value="false" checked={response === false} onChange={() => handleResponseChange(question.id, false)} className="w-5 h-5 text-blue-600 border-slate-300 focus:ring-blue-500" />
                            <span className="text-slate-700 font-medium select-none">No</span>
                        </label>
                    </div>
                );
            default:
                return null;
        }
    };

    if (loading) {
        return <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
    }
    if (error) {
        return <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4"><div className="text-center p-8 bg-white rounded-xl shadow-lg"><AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" /><h3 className="text-xl font-bold text-slate-800 mb-2">Error Loading Survey</h3><p className="text-slate-600">{error}</p></div></div>;
    }
    if (completed) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
                <div className="text-center p-8 sm:p-12 bg-white rounded-2xl shadow-xl max-w-lg w-full">
                    <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-6" />
                    <h2 className="text-3xl font-bold text-slate-800 mb-3">Thank You!</h2>
                    <p className="text-slate-600 leading-relaxed max-w-md mx-auto">
                        Your responses have been sent to <span className="font-semibold text-blue-600">{surveyInfo?.user_name}</span>. They will be in touch shortly. You can now close this window.
                    </p>
                </div>
            </div>
        );
    }
    if (!surveyConfig || !surveyInfo) {
        return null;
    }

    const currentQuestion = surveyConfig.questions[currentStep];
    const progress = ((currentStep + 1) / surveyConfig.questions.length) * 100;

    return (
        <main className="min-h-screen bg-slate-100 flex items-center justify-center p-4 font-sans">
            <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Left Panel: Professional's Info */}
                <aside className="md:col-span-1 p-8 bg-white rounded-2xl shadow-lg flex flex-col items-center text-center">
                    <Avatar
                        name={surveyInfo.user_name}
                        imageUrl={surveyInfo.user_avatar_url}
                        className="w-24 h-24 text-3xl mb-4 border-4 border-slate-200"
                    />
                    <p className="text-sm text-slate-500">A personal request from</p>
                    <h2 className="text-2xl font-bold text-slate-800 mt-1">{surveyInfo.user_name}</h2>
                    <div className="w-16 h-0.5 bg-blue-500 my-6"></div>
                    <p className="text-slate-600 leading-relaxed">
                        "Hi <span className="font-semibold text-blue-600">{surveyInfo.client_name}</span>, thank you for taking a moment to answer these questions. Your thoughts are important to me."
                    </p>
                    {surveyInfo.user_email && (
                        <div className="mt-auto pt-6 text-sm text-slate-500">
                            <p>Questions? Contact me at:</p>
                            <a href={`mailto:${surveyInfo.user_email}`} className="font-medium text-blue-600 hover:underline">{surveyInfo.user_email}</a>
                        </div>
                    )}
                </aside>

                {/* Right Panel: Survey Questions */}
                <div className="md:col-span-2 bg-white p-8 rounded-2xl shadow-lg">
                    <h1 className="text-3xl font-bold text-slate-800 mb-2">{surveyConfig.title}</h1>
                    <p className="text-slate-500 mb-8">{surveyConfig.description}</p>

                    <div className="w-full bg-slate-200 rounded-full h-2 mb-8">
                        <div className="bg-blue-600 h-2 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
                    </div>

                    <div>
                        <h3 className="text-xl font-semibold text-slate-800 mb-2">
                            {currentQuestion.question}
                            {currentQuestion.required && <span className="text-red-500 ml-1">*</span>}
                        </h3>
                        {currentQuestion.help_text && <p className="text-sm text-slate-500 mb-6">{currentQuestion.help_text}</p>}

                        <div className="mt-6">
                            {renderQuestion(currentQuestion)}
                        </div>
                    </div>

                    <div className="flex justify-between items-center mt-10 pt-6 border-t border-slate-200">
                        <button onClick={handlePrevious} disabled={currentStep === 0} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 font-medium rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-50">
                            <ArrowLeft size={16} /> Previous
                        </button>
                        {currentStep < surveyConfig.questions.length - 1 ? (
                            <button onClick={handleNext} disabled={!isStepValid()} className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 shadow-md">
                                Next Question <ArrowRight size={16} />
                            </button>
                        ) : (
                            <button onClick={handleSubmit} disabled={!canSubmit() || submitting} className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 shadow-md">
                                {submitting ? <Loader2 size={18} className="animate-spin" /> : <Send size={16} />}
                                {submitting ? 'Submitting...' : 'Send My Answers'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}