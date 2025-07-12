// frontend/components/conversation/RecommendationActions.tsx
// --- DEFINITIVE FIX: Styling updated to match screenshot, logic remains robust.

'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { Tag, FileText, Loader, CheckCircle, Sparkles } from 'lucide-react';
import { useAppContext, Client } from '@/context/AppContext';

interface RecommendationActionsProps {
  recommendations: any; // This is the 'active_recommendations' object
  client: Client;
  onActionComplete: (updatedClient: Client) => void;
}

export const RecommendationActions = ({ 
  recommendations, 
  client, 
  onActionComplete 
}: RecommendationActionsProps) => {
  const { api } = useAppContext();
  
  const [processingAction, setProcessingAction] = useState<string | null>(null);
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());

  // FIX: Safely access nested properties to prevent runtime errors
  const recommendationList = recommendations?.key_intel?.recommendations || [];
  const intelRec = recommendationList.find((rec: any) => rec.type === 'UPDATE_CLIENT_INTEL');
  
  const { tags_to_add = [], notes_to_add = "" } = intelRec?.payload || {};

  // This memoized value determines if the component should be rendered at all.
  const shouldRender = useMemo(() => {
    const validTags = tags_to_add.filter((tag: string) => tag && !client.user_tags.includes(tag));
    const hasNotes = notes_to_add && !completedActions.has('notes-add');
    return validTags.length > 0 || hasNotes;
  }, [client.user_tags, tags_to_add, notes_to_add, completedActions]);

  // When the underlying recommendations change, reset the local 'completed' state
  useEffect(() => {
    setCompletedActions(new Set());
  }, [recommendations.id]);


  const handleAction = async (actionId: string, tags: string[] = [], notes: string = "") => {
    if (processingAction || completedActions.has(actionId)) return;

    setProcessingAction(actionId);
    try {
      const updatedClient = await api.post(`/api/clients/${client.id}/intel`, {
        tags_to_add: tags,
        notes_to_add: notes,
        active_recommendation_id: recommendations.id, // Pass the slate ID for backend tracking
      });
      
      setCompletedActions(prev => new Set(prev).add(actionId));
      onActionComplete(updatedClient);

    } catch (error) {
      console.error("Failed to perform action:", error);
      alert(`Action failed. Please try again.`);
    } finally {
      setProcessingAction(null);
    }
  };

  if (!intelRec || !shouldRender) {
    return null;
  }

  // FIX: Styling adjusted to precisely match the screenshot's appearance.
  return (
    <div className="bg-gray-700/50 border border-dashed border-blue-400/30 rounded-lg p-3 shadow-lg animate-fade-in-up">
      <h4 className="flex items-center gap-2 text-xs font-bold text-gray-300 mb-3">
        <Sparkles className="w-4 h-4 text-blue-400" />
        AI Suggested Actions
      </h4>
      <div className="flex flex-wrap gap-2">
        {tags_to_add.map((tag: string) => {
          if (!tag || client.user_tags.includes(tag)) return null;
          
          const actionId = `tag-${tag}`;
          const isProcessing = processingAction === actionId;

          return (
            <button
              key={actionId}
              onClick={() => handleAction(actionId, [tag], "")}
              disabled={!!processingAction}
              className="flex items-center gap-1.5 text-sm bg-blue-500/10 text-blue-300 px-2.5 py-1 rounded-md hover:bg-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? <Loader className="w-4 h-4 animate-spin" /> : <Tag className="w-4 h-4" />}
              <span>Add Tag: "{tag}"</span>
            </button>
          );
        })}
        
        {notes_to_add && !completedActions.has('notes-add') && (
          <button
            key="notes-action"
            onClick={() => handleAction('notes-add', [], notes_to_add)}
            disabled={!!processingAction}
            className="flex items-center gap-1.5 text-sm bg-purple-500/10 text-purple-300 px-2.5 py-1 rounded-md hover:bg-purple-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processingAction === 'notes-add' ? <Loader className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            Add Note
          </button>
        )}
      </div>
    </div>
  );
};
