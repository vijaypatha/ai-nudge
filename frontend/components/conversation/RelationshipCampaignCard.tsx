// frontend/components/conversation/RelationshipCampaignCard.tsx
// --- AGNOSTIC VERSION ---
// This component now receives displayConfig to render its title dynamically.

'use client';

import { useState, ReactNode, useEffect } from 'react';
import { Zap, Sparkles, Calendar, Edit2, Loader2, Check, X, PauseCircle, BrainCircuit, ArrowRight } from 'lucide-react';
import { ScheduledMessage, CampaignBriefing } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { EditMessageModal } from './EditMessageModal';
import { ConversationDisplayConfig } from '@/app/(main)/conversations/[clientId]/page';
import { motion } from 'framer-motion';
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';

const ICONS: Record<string, ReactNode> = {
    BrainCircuit: <BrainCircuit className="h-4 w-4 text-gray-400" />,
    Default: <BrainCircuit className="h-4 w-4 text-gray-400" />,
};

interface RelationshipCampaignCardProps {
  plan: CampaignBriefing | null;
  messages: ScheduledMessage[];
  onApprovePlan: (planId: string) => void;
  onDismissPlan: (planId: string) => void;
  isProcessing: boolean;
  isSuccess: boolean;
  onViewScheduled: () => void;
  displayConfig: ConversationDisplayConfig | null; // Expect the config
}

export const RelationshipCampaignCard = ({ plan, messages, onApprovePlan, onDismissPlan, isProcessing, isSuccess, onViewScheduled, displayConfig }: RelationshipCampaignCardProps) => {
  const [editingMessage, setEditingMessage] = useState<ScheduledMessage | null>(null);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  // Add window size tracking for confetti
  useEffect(() => {
    const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // --- DYNAMIC CONFIGURATION ---
  const config = displayConfig?.relationship_campaign || { title: 'Relationship Campaign', icon: 'Default' };
  const defaultIcon = ICONS[config.icon] || ICONS.Default;

  const statusIcons: { [key: string]: JSX.Element } = {
    DRAFT: <Sparkles className="h-4 w-4 text-purple-400" />,
    ACTIVE: <Zap className="h-4 w-4 text-green-400" />,
    PAUSED: <PauseCircle className="h-4 w-4 text-yellow-400" />,
  };
  const statusIcon = plan ? statusIcons[plan.status.toUpperCase()] || defaultIcon : defaultIcon;

  if (!isSuccess && (!plan || !plan.is_plan || plan.status.toUpperCase() !== 'DRAFT')) {
    return (
        <InfoCard title={config.title} icon={defaultIcon}>
             <div className="text-center py-4">
                <p className="text-sm text-gray-400">No new plan suggested.</p>
             </div>
        </InfoCard>
    );
  }
  
  return (
    <>
      {/* Confetti for successful plan activation */}
      {isSuccess && (
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

      {editingMessage && (
        <EditMessageModal
          isOpen={!!editingMessage}
          onClose={() => setEditingMessage(null)}
          message={editingMessage}
          onSaveSuccess={() => setEditingMessage(null)}
        />
      )}
      
      <InfoCard title={config.title} icon={statusIcon}>
        {isSuccess && (
            <div className="p-3 -m-2 rounded-lg bg-green-600/10 text-center animate-fade-in">
                <div className="flex items-center justify-center gap-2 font-semibold text-green-300">
                    <Check className="h-5 w-5" />
                    <p>🎉 Plan Activated!</p>
                </div>
                <p className="text-sm text-green-200 mt-1">Your relationship campaign is now live!</p>
                <button
                    onClick={onViewScheduled}
                    className="mt-3 text-sm text-white font-semibold flex items-center justify-center gap-2 w-full bg-white/10 hover:bg-white/20 py-2 rounded-md transition-colors"
                >
                    View Scheduled Messages <ArrowRight className="h-4 w-4" />
                </button>
            </div>
        )}

        {!isSuccess && plan && (
          <div className="animate-fade-in">
            <h3 className="font-semibold text-white mb-3">{plan.headline}</h3>
            <ul className="space-y-3 pl-1 border-l border-gray-700 ml-1">
              {plan.key_intel.steps?.map((step: any, index: number) => {
                const scheduledDate = new Date();
                scheduledDate.setDate(scheduledDate.getDate() + step.delay_days);
                return (
                    <li key={index} className="text-sm text-gray-300 flex items-start gap-3 pl-4 relative">
                       <div className="absolute -left-[7px] top-1.5 w-3.5 h-3.5 bg-gray-700 rounded-full border-2 border-brand-dark-blue"></div>
                      <div className='flex-1'>
                        <p className="font-semibold text-gray-400 flex items-center gap-2">
                           <Calendar className="h-4 w-4 text-cyan-400/70" />
                           {`Day ${step.delay_days}`}
                        </p>
                        <p className="text-gray-200 mt-1 italic bg-black/20 p-2 rounded-md">"{step.generated_draft || 'Generating draft...'}"</p>
                      </div>
                    </li>
                );
              })}
            </ul>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => onApprovePlan(plan.id)}
                disabled={isProcessing}
                className="flex-1 bg-green-500 text-white px-3 py-1.5 text-sm font-semibold rounded-md hover:bg-green-600 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                Approve Plan
              </button>
              <button 
                onClick={() => onDismissPlan(plan.id)}
                disabled={isProcessing}
                className="bg-gray-700 text-white px-3 py-1.5 text-sm font-semibold rounded-md hover:bg-gray-600 disabled:opacity-50"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
      </InfoCard>
    </>
  );
};
