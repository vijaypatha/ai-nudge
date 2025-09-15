// app/(main)/surveys/[templateId]/page.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2, Edit, BarChart2 } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { SurveyBuilder, Question } from '@/components/survey/SurveyBuilder';
import { SurveyInsights } from '@/components/survey/SurveyInsights';
import { SurveyTemplate } from '../page';
import clsx from 'clsx';

type SurveyView = 'builder' | 'insights';

export default function SurveyDetailPage() {
  const params = useParams();
  const { api } = useAppContext();
  const templateId = params.templateId as string;

  const [template, setTemplate] = useState<SurveyTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<SurveyView>('builder');

  const fetchTemplate = useCallback(async () => {
    if (!templateId) return;
    setLoading(true);
    try {
      const data = await api.get(`/api/surveys/templates/${templateId}`);
      setTemplate(data);
    } catch (err) {
      console.error("Failed to fetch survey template:", err);
      setError("Could not load the survey. It may have been deleted.");
    } finally {
      setLoading(false);
    }
  }, [templateId, api]);

  useEffect(() => {
    fetchTemplate();
  }, [fetchTemplate]);

  const handleTemplateUpdate = useCallback((updatedData: Partial<SurveyTemplate>) => {
    if (!template) return;

    // 1. Optimistically update the UI for a responsive feel
    const newTemplateState = { ...template, ...updatedData };
    setTemplate(newTemplateState);

    // 2. In the background, save metadata changes to the backend
    if (updatedData.name !== undefined || updatedData.description !== undefined) {
      (async () => {
        try {
          await api.put(`/api/surveys/templates/${template.id}`, { 
              name: newTemplateState.name, 
              description: newTemplateState.description 
          });
        } catch (error) {
          console.error("Failed to save template metadata:", error);
          // On error, revert to the original state from the server
          fetchTemplate(); 
        }
      })();
    }
  }, [template, api, fetchTemplate]);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-cyan-400" /></div>;
  }

  if (error) {
     return (
        <div className="p-8 text-center text-red-400">
            <p>{error}</p>
            <Link href="/surveys" className="text-cyan-400 hover:underline mt-4 inline-block">Return to Library</Link>
        </div>
     );
  }

  if (!template) {
    return null;
  }

  return (
    <div className="h-full flex flex-col">
       <header className="px-4 sm:px-6 lg:px-8 pt-4 space-y-4">
        <Link href="/surveys" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-fit">
          <ArrowLeft size={16} />
          Back to Survey Library
        </Link>
        <div className="flex justify-between items-end">
            <div>
                <h1 className="text-2xl font-bold text-white">{template.name}</h1>
                <p className="text-gray-400 text-sm mt-1">{template.description}</p>
            </div>
            <div className="flex items-center gap-2 p-1 bg-black/20 rounded-lg">
                <button onClick={() => setActiveView('builder')} className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors", activeView === 'builder' ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-white/5')}>
                    <Edit size={14} /> Builder
                </button>
                <button onClick={() => setActiveView('insights')} className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors", activeView === 'insights' ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-white/5')}>
                    <BarChart2 size={14} /> Insights
                </button>
            </div>
        </div>
      </header>
      <div className="flex-grow p-4 sm:p-6 lg:p-8">
        {activeView === 'builder' ? (
            <SurveyBuilder 
                key={template.id} 
                template={template} 
                onTemplateUpdate={handleTemplateUpdate} 
            />
        ) : (
            <SurveyInsights templateId={template.id} />
        )}
      </div>
    </div>
  );
}