// frontend/components/survey/SurveyInsights.tsx
// purpose: survey insights component for displaying survey insights

'use client';

import { useState, useEffect, FC } from 'react';
import { useAppContext } from '@/context/AppContext';
import { Loader2, TrendingUp, CheckCircle, Percent, MessageSquare } from 'lucide-react';

interface SurveyInsightsProps {
    templateId: string;
}

interface AnswerInsight {
    answer: string;
    count: number;
}

interface QuestionInsights {
    question_id: string;
    question_text: string;
    question_type: string;
    total_responses: number;
    answers: AnswerInsight[];
}

interface SurveyInsightsData {
    total_sends: number;
    total_completions: number;
    completion_rate: number;
    question_insights: QuestionInsights[];
}

const StatCard: FC<{ icon: React.ReactNode; label: string; value: string | number; color: string }> = ({ icon, label, value, color }) => (
    <div className="bg-brand-primary border border-white/10 rounded-xl p-4 flex items-center gap-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
            {icon}
        </div>
        <div>
            <p className="text-sm text-gray-400">{label}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
        </div>
    </div>
);

const AnswerBar: FC<{ answer: string; count: number; total: number }> = ({ answer, count, total }) => {
    const percentage = total > 0 ? (count / total) * 100 : 0;
    return (
        <div className="text-sm">
            <div className="flex justify-between items-center mb-1 text-gray-300">
                <span className="truncate" title={answer}>{answer}</span>
                <span className="font-semibold">{count}</span>
            </div>
            <div className="w-full bg-black/20 rounded-full h-2">
                <div
                    className="bg-cyan-500 h-2 rounded-full"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
};


export const SurveyInsights: FC<SurveyInsightsProps> = ({ templateId }) => {
    const { api } = useAppContext();
    const [insights, setInsights] = useState<SurveyInsightsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchInsights = async () => {
            if (!templateId) return;
            setLoading(true);
            setError(null);
            try {
                const data = await api.get(`/api/surveys/templates/${templateId}/insights`);
                setInsights(data);
            } catch (err) {
                console.error("Failed to fetch insights:", err);
                setError("Could not load analytics data.");
            } finally {
                setLoading(false);
            }
        };
        fetchInsights();
    }, [templateId, api]);

    if (loading) {
        return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-cyan-400" /></div>;
    }

    if (error) {
        return <div className="p-8 text-center text-red-400">{error}</div>;
    }

    if (!insights) {
        return <div className="p-8 text-center text-gray-400">No data available for this survey yet.</div>;
    }

    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard icon={<TrendingUp size={20} />} label="Total Sends" value={insights.total_sends} color="bg-blue-500/20 text-blue-400" />
                <StatCard icon={<CheckCircle size={20} />} label="Total Completions" value={insights.total_completions} color="bg-green-500/20 text-green-400" />
                <StatCard icon={<Percent size={20} />} label="Completion Rate" value={`${insights.completion_rate.toFixed(1)}%`} color="bg-cyan-500/20 text-cyan-400" />
            </div>

            <div className="space-y-6">
                {insights.question_insights.map((q, index) => (
                    <div key={q.question_id} className="bg-brand-primary border border-white/10 rounded-xl p-5">
                        <p className="font-semibold text-white mb-1">{index + 1}. {q.question_text}</p>
                        <p className="text-xs text-gray-500 mb-4 uppercase flex items-center gap-2">
                            <MessageSquare size={12} /> {q.total_responses} Responses
                        </p>
                        <div className="space-y-3">
                            {q.answers.length > 0 ? (
                                q.answers.slice(0, 5).map(ans => (
                                    <AnswerBar key={ans.answer} answer={ans.answer} count={ans.count} total={q.total_responses} />
                                ))
                            ) : (
                                <p className="text-sm text-gray-500 italic">No responses recorded for this question yet.</p>
                            )}
                            {q.answers.length > 5 && <p className="text-xs text-gray-500 text-center pt-2">+ {q.answers.length - 5} more answers</p>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};