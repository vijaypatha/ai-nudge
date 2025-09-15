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

    // 1. Always update the UI optimistically for a responsive feel
    const newTemplateState = { ...template, ...updatedData };
    setTemplate(newTemplateState);

    // 2. Only save template metadata (name/description) to backend
    // Questions are handled by their individual API endpoints
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
    // Note: We don't need to save questions here because:
    // - handleAddQuestion already persists new questions via POST
    // - handleUpdateQuestion already persists edits via PUT  
    // - handleDeleteQuestion already removes questions via DELETE
    // - We just need to keep the local state in sync
  }, [template, api, fetchTemplate]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-center">
        <div className="text-red-400 mb-4">{error}</div>
        <Link href="/surveys" className="text-cyan-400 hover:text-cyan-300">
          Return to Library
        </Link>
      </div>
    );
  }

  if (!template) {
    return null;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href="/surveys" className="text-gray-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-2xl font-bold text-white">{template.name}</h1>
        </div>
        
        {/* View Toggle */}
        <div className="flex bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setActiveView('builder')}
            className={clsx(
              'px-4 py-2 rounded-md flex items-center gap-2 transition-colors',
              activeView === 'builder' 
                ? 'bg-cyan-500 text-white' 
                : 'text-gray-400 hover:text-white'
            )}
          >
            <Edit className="w-4 h-4" />
            Builder
          </button>
          <button
            onClick={() => setActiveView('insights')}
            className={clsx(
              'px-4 py-2 rounded-md flex items-center gap-2 transition-colors',
              activeView === 'insights' 
                ? 'bg-cyan-500 text-white' 
                : 'text-gray-400 hover:text-white'
            )}
          >
            <BarChart2 className="w-4 h-4" />
            Insights
          </button>
        </div>
      </div>

      {/* Content */}
      {activeView === 'builder' ? (
        <SurveyBuilder 
          template={template} 
          onTemplateUpdate={handleTemplateUpdate}
        />
      ) : (
        <SurveyInsights templateId={templateId} />
      )}
    </div>
  );
}
