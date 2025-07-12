// frontend/components/conversation/CoPilotBriefingCard.tsx

'use client';

import React from 'react';
import { CampaignBriefing } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { Lightbulb, Check, RefreshCw } from 'lucide-react';

interface CoPilotBriefingCardProps {
  briefing: CampaignBriefing;
  // onAction: (actionType: string, briefingId: string) => void; // Future implementation
}

export const CoPilotBriefingCard = ({ briefing }: CoPilotBriefingCardProps) => {
  const actions = briefing.key_intel.actions || [];

  const getIconForAction = (type: string) => {
    switch (type) {
      case 'UPDATE_PLAN': return <RefreshCw className="w-4 h-4" />;
      case 'END_PLAN': return <Check className="w-4 h-4" />;
      default: return <Lightbulb className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-yellow-900/40 border border-dashed border-yellow-500/50 rounded-lg p-3 shadow-lg animate-fade-in-up">
      <h4 className="flex items-center gap-2 text-xs font-bold text-yellow-300 mb-2">
        <Lightbulb className="w-4 h-4 text-yellow-400" />
        Co-Pilot Suggestion
      </h4>
      <p className="text-sm text-yellow-200/90 mb-4">{briefing.original_draft}</p>
      <div className="flex flex-wrap gap-2">
        {actions.map((action: any) => (
          <Button
            key={action.type}
            // onClick={() => onAction(action.type, briefing.id)}
            variant="secondary"
            className="bg-yellow-500/10 text-yellow-200 hover:bg-yellow-500/20"
          >
            {getIconForAction(action.type)}
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
};