// frontend/components/conversation/CoPilotBriefingCard.tsx

'use client';

import React, { useState } from 'react';
import { CampaignBriefing } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { Lightbulb, Check, RefreshCw, Loader } from 'lucide-react';
import { useAppContext } from '@/context/AppContext'; // Assuming you have this for API calls

interface CoPilotBriefingCardProps {
  briefing: CampaignBriefing;
  onActionSuccess: () => void; // Prop to notify parent to refetch data
}

export const CoPilotBriefingCard = ({ briefing, onActionSuccess }: CoPilotBriefingCardProps) => {
  const { api } = useAppContext();
  const [processingAction, setProcessingAction] = useState<string | null>(null);

  const actions = briefing.key_intel.actions || [];

  const getIconForAction = (type: string) => {
    if (processingAction === type) {
      return <Loader className="w-4 h-4 animate-spin" />;
    }
    switch (type) {
      case 'UPDATE_PLAN': return <RefreshCw className="w-4 h-4" />;
      case 'END_PLAN': return <Check className="w-4 h-4" />;
      default: return <Lightbulb className="w-4 h-4" />;
    }
  };

  const handleAction = async (actionType: string) => {
    if (processingAction) return; // Prevent multiple clicks
    setProcessingAction(actionType);
    try {
      await api.post(`/api/campaigns/${briefing.id}/action`, {
        action_type: actionType,
      });
      // On success, call the parent's callback function to refresh the conversation view
      onActionSuccess();
    } catch (error) {
      console.error(`Failed to perform action ${actionType}`, error);
      // Optionally, show an error toast to the user
      alert(`Error: Could not ${actionType === 'UPDATE_PLAN' ? 'update' : 'end'} the plan.`);
    } finally {
      setProcessingAction(null);
    }
  };

  return (
    <div className="bg-yellow-900/40 border border-dashed border-yellow-500/50 rounded-lg p-4 my-4 shadow-lg animate-fade-in-up">
      <h4 className="flex items-center gap-2 text-sm font-bold text-yellow-300 mb-2">
        <Lightbulb className="w-4 h-4 text-yellow-400" />
        Co-Pilot Suggestion
      </h4>
      <p className="text-sm text-yellow-200/90 mb-4">{briefing.original_draft}</p>
      <div className="flex flex-wrap gap-3">
        {actions.map((action: any) => (
          <Button
            key={action.type}
            onClick={() => handleAction(action.type)}
            disabled={!!processingAction}
            variant="secondary"
            className="bg-yellow-500/10 text-yellow-200 hover:bg-yellow-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {getIconForAction(action.type)}
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
};