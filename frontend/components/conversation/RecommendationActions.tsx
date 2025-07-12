// frontend/components/conversation/RecommendationActions.tsx
// --- CORRECTED: Uses the new consolidated backend endpoint and fixes data paths.

'use client';

import React, { useState } from 'react';
import { Plus, Loader, Tag, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { Client } from '@/context/AppContext';

interface RecommendationActionsProps {
  recommendations: any;
  client: Client;
  onActionComplete: () => void;
}

export const RecommendationActions = ({ 
  recommendations, 
  client, 
  onActionComplete 
}: RecommendationActionsProps) => {
  const { api } = useAppContext();
  
  const [processingActions, setProcessingActions] = useState<Set<string>>(new Set());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // --- FIX: The recommendations array is inside the 'key_intel' object ---
  const recommendationList = recommendations?.key_intel?.recommendations || [];

  const handleAction = async (actionId: string, tags: string[] = [], notes: string = "") => {
    if (processingActions.has(actionId)) return;

    setProcessingActions(prev => new Set(prev).add(actionId));
    setErrorMessage(null);

    try {
      // --- FIX: Call the new single, powerful endpoint ---
      await api.post(`/api/clients/${client.id}/intel`, {
        tags_to_add: tags,
        notes_to_add: notes,
        active_recommendation_id: recommendations.id // Pass the slate ID to clear it
      });
      onActionComplete();
    } catch (error) {
      console.error("Failed to perform action:", error);
      setErrorMessage(`Action failed. Please try again.`);
      setTimeout(() => setErrorMessage(null), 5000);
      setProcessingActions(prev => {
          const newSet = new Set(prev);
          newSet.delete(actionId);
          return newSet;
      });
    }
  };
  
  const intelRec = recommendationList.find((rec: any) => rec.type === 'UPDATE_CLIENT_INTEL');
  if (!intelRec) return null;

  const { tags_to_add = [], notes_to_add = "" } = intelRec.payload;

  if (tags_to_add.length === 0 && !notes_to_add) {
    return null;
  }

  return (
    <div className="mx-6 mb-2 bg-gradient-to-r from-blue-500/5 to-indigo-500/5 border border-blue-200/20 rounded-lg p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 bg-primary-action rounded-full animate-pulse"></div>
        <h4 className="text-sm font-semibold text-brand-text-main">
          AI Suggested Actions
        </h4>
      </div>
      
      {errorMessage && (
        <div className="flex items-center gap-2 mb-3 p-2 bg-red-500/10 border border-red-500/20 rounded-md">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span className="text-sm text-red-400">{errorMessage}</span>
        </div>
      )}
      
      <div className="flex flex-wrap gap-2">
        {tags_to_add.map((tag: string) => {
          if (!tag) return null;
          const actionId = `tag-${tag}`;
          const isProcessing = processingActions.has(actionId);
          const tagExists = client.user_tags.includes(tag);

          return (
            <button
              key={actionId}
              onClick={() => handleAction(actionId, [tag], "")}
              disabled={isProcessing || tagExists}
              className="flex items-center gap-1.5 text-sm bg-primary-action/10 text-primary-action px-2 py-1 rounded-md hover:bg-primary-action/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? <Loader className="w-4 h-4 animate-spin" /> : <Tag className="w-4 h-4" />}
              {tagExists ? `Tag exists: "${tag}"` : `Add Tag: "${tag}"`}
            </button>
          );
        })}
        
        {notes_to_add && (
          <button
            key="notes-action"
            onClick={() => handleAction('notes-add', [], notes_to_add)}
            disabled={processingActions.has('notes-add')}
            className="flex items-center gap-1.5 text-sm bg-purple-500/10 text-purple-300 px-2 py-1 rounded-md hover:bg-purple-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processingActions.has('notes-add') ? <Loader className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            Add Note
          </button>
        )}
      </div>
    </div>
  );
};