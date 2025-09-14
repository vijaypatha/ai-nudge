'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Loader2, BookOpen } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { SurveyCard } from '@/components/survey/SurveyCard';

// This interface defines the structure of a survey template object
export interface SurveyTemplate {
  id: string;
  name: string;
  description: string | null;
  questions: any[]; // Using 'any[]' for now, can be replaced with a strict Question type
}

export default function SurveyLibraryPage() {
  const { api } = useAppContext();
  const router = useRouter();
  const [templates, setTemplates] = useState<SurveyTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  // Fetch all survey templates from the backend when the component mounts
  useEffect(() => {
    const fetchTemplates = async () => {
      setIsLoading(true);
      try {
        const data = await api.get('/api/surveys/templates');
        setTemplates(data);
      } catch (error) {
        console.error("Failed to fetch survey templates:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTemplates();
  }, [api]);

  // Handles the creation of a new survey template
  const handleCreateSurvey = async () => {
    setIsCreating(true);
    try {
      // Create a new template with a default name and navigate to the builder
      const newTemplate = await api.post('/api/surveys/templates', {
        name: 'Untitled Survey',
        description: 'Add a description for your clients.'
      });
      if (newTemplate && newTemplate.id) {
        router.push(`/surveys/${newTemplate.id}`);
      }
    } catch (error) {
      console.error("Failed to create survey:", error);
      alert("Could not create a new survey. Please try again.");
    } finally {
      setIsCreating(false);
    }
  };

  // Display a loading spinner while fetching data
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <header className="flex justify-between items-center mb-8">
        <div>
            <h1 className="text-3xl font-bold text-white">Survey Library</h1>
            <p className="text-gray-400 mt-1">Create and manage your client intake surveys.</p>
        </div>
        <button 
          onClick={handleCreateSurvey} 
          disabled={isCreating}
          className="flex items-center gap-2 px-4 py-2 bg-primary-action text-brand-dark rounded-lg text-sm font-semibold hover:brightness-110 transition-transform transform active:scale-95 disabled:opacity-50"
        >
          {isCreating ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
          {isCreating ? 'Creating...' : 'Create Survey'}
        </button>
      </header>

      {templates.length === 0 ? (
        <div className="text-center py-20 px-6 border-2 border-dashed border-white/10 rounded-xl bg-black/10">
          <BookOpen size={48} className="mx-auto text-gray-500 mb-4" />
          <h3 className="text-xl font-semibold text-white">Your library is empty</h3>
          <p className="text-gray-400 mt-2">Click "Create Survey" to build your first intake form.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {templates.map(template => (
            <SurveyCard key={template.id} template={template} />
          ))}
        </div>
      )}
    </div>
  );
}
