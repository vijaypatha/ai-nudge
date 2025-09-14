'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { SurveyBuilder } from '@/components/survey/SurveyBuilder';
import { SurveyTemplate } from '../page';

export default function SurveyBuilderPage() {
  const params = useParams();
  const router = useRouter();
  const { api } = useAppContext();
  const templateId = params.templateId as string;

  const [template, setTemplate] = useState<SurveyTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  
  const handleTemplateUpdate = (updatedTemplate: SurveyTemplate) => {
    setTemplate(updatedTemplate);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-cyan-400" /></div>;
  }
  
  if (error) {
     return (
        <div className="p-8 text-center text-red-400">
            <p>{error}</p>
            <Link href="/surveys" className="text-cyan-400 hover:underline mt-4 inline-block">
                Return to Library
            </Link>
        </div>
     );
  }

  if (!template) {
    return null; // Should be handled by loading/error states
  }

  return (
    <div className="h-full flex flex-col">
       <header className="px-4 sm:px-6 lg:px-8 pt-4">
        <Link href="/surveys" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-fit">
          <ArrowLeft size={16} />
          Back to Survey Library
        </Link>
      </header>
      <div className="flex-grow p-4 sm:p-6 lg:p-8">
        <SurveyBuilder key={template.id} initialTemplate={template} onUpdate={handleTemplateUpdate} />
      </div>
    </div>
  );
}
