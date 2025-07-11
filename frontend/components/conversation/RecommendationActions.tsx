// frontend/components/conversation/RecommendationActions.tsx
// --- NEW FILE ---

'use client';

import React, { useState } from 'react';
import { Plus, Loader } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { Client } from '@/context/AppContext';

interface RecommendationActionsProps {
  recommendations: any;
  client: Client;
  onActionComplete: () => void;
}

export const RecommendationActions = ({ recommendations, client, onActionComplete }: RecommendationActionsProps) => {
  const { api } = useAppContext();
  const [addingTag, setAddingTag] = useState<string | null>(null);

  if (!recommendations?.key_intel?.recommendations) {
    return null;
  }

  const intelRec = recommendations.key_intel.recommendations.find(
    (rec: any) => rec.type === 'UPDATE_CLIENT_INTEL'
  );

  if (!intelRec || !intelRec.payload?.tags_to_add?.length) {
    return null;
  }

  const handleAddTag = async (tag: string) => {
    setAddingTag(tag);
    try {
      await api.post(`/api/clients/${client.id}/tags`, { tags: [tag] });
      onActionComplete();
    } catch (error) {
      console.error("Failed to add tag:", error);
      alert(`Failed to add tag: ${tag}`);
    } finally {
      setAddingTag(null);
    }
  };

  return (
    <div className="mx-6 mb-2 p-3 border border-dashed border-primary-action/30 rounded-lg bg-brand-dark/30">
      <h4 className="text-xs font-bold text-brand-text-muted mb-2">✨ AI Suggestions</h4>
      <div className="flex flex-wrap gap-2">
        {intelRec.payload.tags_to_add.map((tag: string) => {
          if (client.user_tags.includes(tag)) {
            return null;
          }
          return (
            <button
              key={tag}
              onClick={() => handleAddTag(tag)}
              disabled={!!addingTag}
              className="flex items-center gap-1.5 text-sm bg-primary-action/10 text-primary-action px-2 py-1 rounded-md hover:bg-primary-action/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {addingTag === tag ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Add Tag: "{tag}"
            </button>
          );
        })}
      </div>
    </div>
  );
};