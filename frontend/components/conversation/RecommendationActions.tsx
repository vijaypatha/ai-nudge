// frontend/components/conversation/RecommendationActions.tsx
// --- DEFINITIVE FIX: Passes the slate ID for tracking and relies on local state for UI updates.

'use client';

import React, { useState, useMemo } from 'react';
import { Plus, Loader, Tag, FileText, CheckCircle } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { Client } from '@/context/AppContext';

interface RecommendationActionsProps {
  recommendations: any; // This is the 'active_recommendations' object, which includes the slate's 'id'
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

  const recommendationList = recommendations?.key_intel?.recommendations || [];
  const intelRec = recommendationList.find((rec: any) => rec.type === 'UPDATE_CLIENT_INTEL');
  
  const { tags_to_add = [], notes_to_add = "" } = intelRec?.payload || {};

  // This function determines if the entire component should disappear based on local and parent state.
  const allActionsCompletedOrRedundant = useMemo(() => {
    // Filter out tags that are empty or already exist on the client profile.
    const suggestedTags = tags_to_add.filter((tag: string) => tag && !client.user_tags.includes(tag));
    // Check if there are notes to add and if the notes-add action has been completed.
    const hasPendingNotes = notes_to_add && !completedActions.has('notes-add');
    // If there are no more valid tags to suggest and no pending notes, the component can be hidden.
    return suggestedTags.length === 0 && !hasPendingNotes;
  }, [client.user_tags, tags_to_add, notes_to_add, completedActions]);


  const handleAction = async (actionId: string, tags: string[] = [], notes: string = "") => {
    if (processingAction || completedActions.has(actionId)) return;

    setProcessingAction(actionId);
    try {
      // --- MODIFICATION START ---
      // The payload now includes the recommendation slate's ID for better tracking.
      const updatedClient = await api.post(`/api/clients/${client.id}/intel`, {
        tags_to_add: tags,
        notes_to_add: notes,
        active_recommendation_id: recommendations.id, // Pass the slate ID
      });
      // --- MODIFICATION END ---
      
      // Mark this specific action as completed in the local state
      setCompletedActions(prev => new Set(prev).add(actionId));
      // Pass the updated client data back to the parent to refresh the UI
      onActionComplete(updatedClient);

    } catch (error) {
      console.error("Failed to perform action:", error);
      alert(`Action failed. Please try again.`);
    } finally {
      // Allow other buttons to be clicked
      setProcessingAction(null);
    }
  };

  // If there are no recommendations to show or they've all been actioned, hide the component.
  if (!intelRec || allActionsCompletedOrRedundant) {
    return null;
  }

  return (
    <div className="mx-6 mb-2 bg-brand-dark/30 border border-dashed border-primary-action/30 rounded-lg p-4 shadow-sm">
      <h4 className="text-xs font-bold text-brand-text-muted mb-2">✨ AI Suggested Actions</h4>
      <div className="flex flex-wrap gap-2">
        {tags_to_add.map((tag: string) => {
          if (!tag) return null;
          const actionId = `tag-${tag}`;
          const isProcessing = processingAction === actionId;
          const isCompleted = completedActions.has(actionId);
          
          // Check against the current client object for real-time accuracy.
          // This ensures that if a tag is added, its corresponding button disappears.
          const tagExists = client.user_tags.includes(tag);

          // Don't render the button if the tag has been added
          if (tagExists) return null;

          return (
            <button
              key={actionId}
              onClick={() => handleAction(actionId, [tag], "")}
              disabled={!!processingAction}
              className="flex items-center gap-1.5 text-sm bg-primary-action/10 text-primary-action px-2 py-1 rounded-md hover:bg-primary-action/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? <Loader className="w-4 h-4 animate-spin" /> : isCompleted ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Tag className="w-4 h-4" />}
              {isCompleted ? "Tag Added!" : `Add Tag: "${tag}"`}
            </button>
          );
        })}
        
        {notes_to_add && !completedActions.has('notes-add') && (
          <button
            key="notes-action"
            onClick={() => handleAction('notes-add', [], notes_to_add)}
            disabled={!!processingAction}
            className="flex items-center gap-1.5 text-sm bg-purple-500/10 text-purple-300 px-2 py-1 rounded-md hover:bg-purple-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processingAction === 'notes-add' ? <Loader className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            Add Note
          </button>
        )}
      </div>
    </div>
  );
};