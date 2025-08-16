'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, ArrowRight, ArrowLeft, Loader2, Send, AlertCircle } from 'lucide-react';

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

    // Load survey information and configuration
    useEffect(() => {
        const loadSurvey = async () => {
            setLoading(true);
            setError(null);
            try {
                // Get survey info (client, user, survey type)
                const infoResponse = await fetch(`http://localhost:8001/api/surveys/public/info/${surveyId}`);
                if (!infoResponse.ok) {
                    const errorData = await infoResponse.json();
                    throw new Error(errorData.detail || 'Survey not found or expired');
                }
                const info = await infoResponse.json();
                setSurveyInfo(info);

                // --- THIS IS THE FIX ---
                // We must pass the survey_id as a query parameter so the backend can
                // fetch the correct user's custom survey configuration.
                const configResponse = await fetch(`http://localhost:8001/api/surveys/public/config/${info.survey_type}?survey_id=${surveyId}`);
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
            // Submit survey responses
            const response = await fetch(`http://localhost:8001/api/surveys/public/response/${surveyId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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

        switch (question.type) {
            case 'text':
                return (
                    <input
                        type="text"
                        value={response || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                        placeholder={question.placeholder}
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-gray-400 focus:border-cyan-400 focus:outline-none"
                    />
                );

            case 'number':
                return (
                    <input
                        type="number"
                        value={response || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                        placeholder={question.placeholder}
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-gray-400 focus:border-cyan-400 focus:outline-none"
                    />
                );

            case 'select':
                return (
                    <select
                        value={response || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white focus:border-cyan-400 focus:outline-none"
                    >
                        <option value="">Select an option...</option>
                        {question.options?.map((option) => (
                            <option key={option} value={option} className="bg-gray-800">
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
                                <span className="text-sm text-gray-300">{option}</span>
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
                            <span className="text-sm text-gray-300">Yes</span>
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
                            <span className="text-sm text-gray-300">No</span>
                        </label>
                    </div>
                );

            default:
                return null;
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
                <div className="bg-glass-card p-8 rounded-lg shadow-2xl max-w-md w-full text-center border border-white/10">
                    <div className="flex items-center justify-center gap-3 mb-4">
                        <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
                        <span className="text-gray-300">Loading survey...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
                <div className="bg-glass-card p-8 rounded-lg shadow-2xl max-w-md w-full text-center border border-white/10">
                    <div className="flex items-center justify-center gap-3 mb-4 text-red-400">
                        <AlertCircle className="w-6 h-6" />
                        <span className="font-medium">Error</span>
                    </div>
                    <p className="text-gray-400 mb-4">{error}</p>
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

    if (completed) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
                <div className="bg-glass-card p-8 rounded-lg shadow-2xl max-w-md w-full text-center border border-white/10">
                    <div className="flex items-center justify-center gap-3 mb-4 text-green-400">
                        <CheckCircle className="w-8 h-8" />
                        <span className="text-xl font-bold">Thank You!</span>
                    </div>
                    <p className="text-gray-300 mb-4">
                        Your survey responses have been submitted successfully. 
                        {surveyInfo?.user_name} will review your preferences and get back to you soon.
                    </p>
                    <div className="text-xs text-gray-500">
                        You can close this window now.
                    </div>
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
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4">
            <div className="max-w-2xl mx-auto">
                <div className="bg-glass-card rounded-lg shadow-2xl p-6 border border-white/10">
                    {/* Header */}
                    <div className="text-center mb-6">
                        <h1 className="text-2xl font-bold text-white mb-2">{surveyConfig.title}</h1>
                        <p className="text-gray-400 text-sm mb-4">{surveyConfig.description}</p>
                        
                        {/* Client/User Info */}
                        <div className="bg-cyan-500/10 p-3 rounded-lg mb-4 border border-cyan-500/20">
                            <p className="text-sm text-gray-300">
                                Hi <span className="font-medium text-cyan-400">{surveyInfo.client_name}</span>! 
                                <span className="text-cyan-400">{surveyInfo.user_name}</span> has requested this survey to better serve you.
                            </p>
                        </div>
                        
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
                            <div className="w-6 h-6 bg-gradient-to-r from-cyan-400 to-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-1">
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
                            onClick={handlePrevious}
                            disabled={currentStep === 0}
                            className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <ArrowLeft size={16} />
                            Previous
                        </button>

                        <div className="flex gap-3">
                            {currentStep < surveyConfig.questions.length - 1 ? (
                                <button
                                    onClick={handleNext}
                                    disabled={!canGoNext()}
                                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:from-cyan-600 hover:to-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Next
                                    <ArrowRight size={16} />
                                </button>
                            ) : (
                                <button
                                    onClick={handleSubmit}
                                    disabled={!canSubmit() || submitting}
                                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:from-cyan-600 hover:to-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
            </div>
        </div>
    );
}
