// frontend/components/survey/ClientIntakeSurvey.tsx
// Purpose: Client intake survey component for gathering initial preferences

'use client';

import { useState, useEffect } from 'react';
import { useAppContext } from '@/context/AppContext';
import { CheckCircle, ArrowRight, ArrowLeft, Loader2, Send } from 'lucide-react';

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

interface ClientIntakeSurveyProps {
    clientId: string;
    surveyType?: string;
    onComplete?: (preferences: any, tags: string[]) => void;
    onCancel?: () => void;
}

export const ClientIntakeSurvey = ({ 
    clientId, 
    surveyType, 
    onComplete, 
    onCancel 
}: ClientIntakeSurveyProps) => {
    const { api } = useAppContext();
    const [surveyConfig, setSurveyConfig] = useState<SurveyConfig | null>(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [responses, setResponses] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load survey configuration
    useEffect(() => {
        const loadSurveyConfig = async () => {
            setLoading(true);
            setError(null);
            try {
                // Determine survey type if not provided
                let type = surveyType;
                if (!type) {
                    // Get client info to determine type
                    const client = await api.get(`/api/clients/${clientId}`);
                    const user = await api.get('/api/users/me');
                    
                    // Simple logic to determine survey type
                    if (user.vertical === 'therapy') {
                        type = 'therapy';
                    } else {
                        type = 'real_estate_buyer'; // Default
                    }
                }
                
                const config = await api.get(`/api/surveys/config/${type}`);
                setSurveyConfig(config);
            } catch (err: any) {
                setError(err.message || 'Failed to load survey');
            } finally {
                setLoading(false);
            }
        };

        loadSurveyConfig();
    }, [clientId, surveyType, api]);

    const handleResponseChange = (questionId: string, value: any) => {
        setResponses(prev => ({
            ...prev,
            [questionId]: value
        }));
    };

    const handleMultiSelectChange = (questionId: string, option: string) => {
        setResponses(prev => {
            const currentValues = prev[questionId] || [];
            const newValues = currentValues.includes(option)
                ? currentValues.filter((v: string) => v !== option)
                : [...currentValues, option];
            return {
                ...prev,
                [questionId]: newValues
            };
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
        
        // Check if all required questions are answered
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
            // --- THIS IS THE FIX ---
            // Call the new, dedicated endpoint for manual survey submissions.
            await api.post(`/api/surveys/manual-submission/${clientId}`, responses);
            
            if (onComplete) {
                // onComplete triggers a client data refresh in the parent component.
                onComplete({}, []); 
            }
        } catch (err: any) {
            setError(err.message || 'Failed to submit survey');
        } finally {
            setSubmitting(false);
        }
    };

    const renderQuestion = (question: SurveyQuestion) => {
        const response = responses[question.id];

        switch (question.type) {
            case 'text':
                return (
                    <input
                        type="text"
                        value={response || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                        placeholder={question.placeholder}
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:border-cyan-400 focus:outline-none"
                    />
                );

            case 'number':
                return (
                    <input
                        type="number"
                        value={response || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                        placeholder={question.placeholder}
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:border-cyan-400 focus:outline-none"
                    />
                );

            case 'select':
                return (
                    <select
                        value={response || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:border-cyan-400 focus:outline-none"
                    >
                        <option value="">Select an option...</option>
                        {question.options?.map((option) => (
                            <option key={option} value={option}>
                                {option}
                            </option>
                        ))}
                    </select>
                );

            case 'multi_select':
                return (
                    <div className="space-y-2">
                        {question.options?.map((option) => (
                            <label key={option} className="flex items-center gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={response?.includes(option) || false}
                                    onChange={() => handleMultiSelectChange(question.id, option)}
                                    className="w-4 h-4 text-cyan-400 bg-black/20 border-white/10 rounded focus:ring-cyan-400"
                                />
                                <span className="text-sm">{option}</span>
                            </label>
                        ))}
                    </div>
                );

            case 'boolean':
                return (
                    <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name={question.id}
                                value="true"
                                checked={response === true}
                                onChange={() => handleResponseChange(question.id, true)}
                                className="w-4 h-4 text-cyan-400 bg-black/20 border-white/10 focus:ring-cyan-400"
                            />
                            <span className="text-sm">Yes</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name={question.id}
                                value="false"
                                checked={response === false}
                                onChange={() => handleResponseChange(question.id, false)}
                                className="w-4 h-4 text-cyan-400 bg-black/20 border-white/10 focus:ring-cyan-400"
                            />
                            <span className="text-sm">No</span>
                        </label>
                    </div>
                );

            default:
                return null;
        }
    };

    if (loading) {
        return (
            <div className="bg-glass-card p-6 rounded-lg">
                <div className="flex items-center justify-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                    <span className="text-sm">Loading survey...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-glass-card p-6 rounded-lg">
                <div className="text-center">
                    <p className="text-red-400 text-sm mb-4">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-cyan-500 text-white rounded-lg text-sm hover:bg-cyan-600 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    if (!surveyConfig) {
        return null;
    }

    const currentQuestion = surveyConfig.questions[currentStep];
    const progress = ((currentStep + 1) / surveyConfig.questions.length) * 100;

    return (
        <div className="bg-glass-card p-6 rounded-lg max-w-2xl mx-auto">
            {/* Header */}
            <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-white mb-2">{surveyConfig.title}</h2>
                <p className="text-gray-400 text-sm mb-4">{surveyConfig.description}</p>
                
                {/* Progress bar */}
                <div className="w-full bg-white/10 rounded-full h-2 mb-4">
                    <div 
                        className="bg-gradient-to-r from-cyan-400 to-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    />
                </div>
                
                <p className="text-xs text-gray-500">
                    Question {currentStep + 1} of {surveyConfig.questions.length} • {surveyConfig.estimated_time}
                </p>
            </div>

            {/* Question */}
            <div className="mb-6">
                <div className="flex items-start gap-3 mb-4">
                    <div className="w-6 h-6 bg-cyan-400 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-1">
                        {currentStep + 1}
                    </div>
                    <div className="flex-1">
                        <h3 className="text-white font-medium mb-2">
                            {currentQuestion.question}
                            {currentQuestion.required && <span className="text-red-400 ml-1">*</span>}
                        </h3>
                        {currentQuestion.help_text && (
                            <p className="text-gray-400 text-sm mb-3">{currentQuestion.help_text}</p>
                        )}
                        {renderQuestion(currentQuestion)}
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center">
                <button
                    onClick={onCancel}
                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors text-sm"
                >
                    Cancel
                </button>

                <div className="flex gap-3">
                    {currentStep > 0 && (
                        <button
                            onClick={handlePrevious}
                            className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20 transition-colors"
                        >
                            <ArrowLeft size={16} />
                            Previous
                        </button>
                    )}

                    {currentStep < surveyConfig.questions.length - 1 ? (
                        <button
                            onClick={handleNext}
                            disabled={!canGoNext()}
                            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg text-sm hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                            <ArrowRight size={16} />
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            disabled={!canSubmit() || submitting}
                            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg text-sm hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Submitting...
                                </>
                            ) : (
                                <>
                                    <Send size={16} />
                                    Submit Survey
                                </>
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
