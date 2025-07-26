// frontend/components/conversation/CoPilotBriefingCard.tsx

'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CampaignBriefing } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { Lightbulb, Check, RefreshCw, Loader } from 'lucide-react';
import { useAppContext } from '@/context/AppContext'; // Assuming you have this for API calls
import { InfoCard } from '@/components/ui/InfoCard';
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';

interface CoPilotBriefingCardProps {
  briefing: CampaignBriefing;
  onActionSuccess: () => void; // Prop to notify parent to refetch data
}

export const CoPilotBriefingCard = ({ briefing, onActionSuccess }: CoPilotBriefingCardProps) => {
  const { api } = useAppContext();
  const [processingAction, setProcessingAction] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  // Add window size tracking for confetti
  useEffect(() => {
    const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
      
      // Show confetti on success
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 7000); // Hide after 7 seconds
      
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
    <>
      {/* Confetti for successful action completion */}
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={600}
          tweenDuration={7000}
          colors={[
            ACTIVE_THEME.primary.from,
            ACTIVE_THEME.primary.to,
            ACTIVE_THEME.accent,
            ACTIVE_THEME.action,
            '#ffffff'
          ]}
        />
      )}

      <InfoCard title="AI Co-Pilot Briefing" icon="BrainCircuit">
        <div className="space-y-4">
          <div className="text-sm text-gray-300">
            {briefing.key_intel.summary}
          </div>
          
          {actions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-white">Recommended Actions:</h4>
              <div className="flex flex-wrap gap-2">
                {actions.map((action: any, index: number) => (
                  <button
                    key={index}
                    onClick={() => handleAction(action.type)}
                    disabled={processingAction !== null}
                    className="flex items-center gap-2 px-3 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-md transition-colors disabled:opacity-50"
                  >
                    {getIconForAction(action.type)}
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </InfoCard>
    </>
  );
};