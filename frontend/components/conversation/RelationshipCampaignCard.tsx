// frontend/components/conversation/RelationshipCampaignCard.tsx
// --- DEFINITIVE FIX V2: Separates render logic for DRAFT and ACTIVE states for robustness.

'use client';

import { useState } from 'react';
import { Zap, Sparkles, Calendar, Edit2, Loader2, Check, X, PauseCircle, BrainCircuit } from 'lucide-react';
import { ScheduledMessage, CampaignBriefing } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { EditMessageModal } from './EditMessageModal';
import clsx from 'clsx';

interface RelationshipCampaignCardProps {
  plan: CampaignBriefing | null;
  messages: ScheduledMessage[];
  onApprovePlan: (planId: string) => void;
  onDismissPlan: (planId: string) => void;
  isProcessing: boolean;
}

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

export const RelationshipCampaignCard = ({ plan, messages, onApprovePlan, onDismissPlan, isProcessing }: RelationshipCampaignCardProps) => {
  const [editingMessage, setEditingMessage] = useState<ScheduledMessage | null>(null);

  const statusIcons: { [key: string]: JSX.Element } = {
    DRAFT: <Sparkles className="h-4 w-4 text-purple-400" />,
    ACTIVE: <Zap className="h-4 w-4 text-green-400" />,
    PAUSED: <PauseCircle className="h-4 w-4 text-yellow-400" />,
    COMPLETED: <Check className="h-4 w-4 text-gray-500" />,
    CANCELLED: <X className="h-4 w-4 text-gray-500" />,
  };
  const statusIcon = plan ? statusIcons[plan.status.toUpperCase()] || <BrainCircuit className="h-4 w-4 text-gray-400" /> : <BrainCircuit className="h-4 w-4 text-gray-400" />;

  const hasContent = plan || messages.length > 0;

  return (
    <>
      {editingMessage && (
        <EditMessageModal
          isOpen={!!editingMessage}
          onClose={() => setEditingMessage(null)}
          message={editingMessage}
        />
      )}
      
      <InfoCard title="Relationship Campaign" icon={statusIcon}>
        {!plan && (
          <div className="text-center py-4">
            <p className="text-sm text-gray-400 mb-3">No campaign planned for this client.</p>
          </div>
        )}
        
        {plan && plan.is_plan && (
          <div className={clsx(
              "p-3 -m-2 rounded-lg transition-colors",
              // --- FIX: Conditional green background for ACTIVE/PAUSED plans ---
              plan.status !== 'DRAFT' && 'bg-green-600/10' 
          )}>
            <h3 className="font-semibold text-white mb-3">{plan.headline}</h3>
            <ul className="space-y-3 pl-1 border-l border-gray-700 ml-1">
              
              {/* --- FIX: Separate render logic for DRAFT plans --- */}
              {plan.status === 'DRAFT' && plan.key_intel.steps?.map((step: any) => {
                const scheduledDate = new Date();
                scheduledDate.setDate(scheduledDate.getDate() + step.delay_days);
                return (
                  <li key={step.name} className="text-sm text-gray-300 flex items-start gap-3 pl-4 relative">
                    <div className="absolute -left-[7px] top-1.5 w-3.5 h-3.5 bg-gray-700 rounded-full border-2 border-brand-dark-blue"></div>
                    <div className='flex-1'>
                      <p className="font-semibold text-gray-400 flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-cyan-400/70" />
                        {/* Show calculated future date */}
                        {formatDate(scheduledDate.toISOString())} 
                      </p>
                      <p className="text-gray-200 mt-1 italic bg-black/20 p-2 rounded-md">"{step.generated_draft || 'Generating draft...'}"</p>
                    </div>
                  </li>
                );
              })}

              {/* --- FIX: Separate render logic for ACTIVE/PAUSED plans --- */}
              {plan.status !== 'DRAFT' && messages.map(msg => {
                // Find the original step name to provide context
                const step = plan.key_intel.steps?.find((s: any) => s.name === msg.playbook_touchpoint_id);
                return (
                  <li key={msg.id} className="text-sm text-gray-300 flex items-start gap-3 pl-4 relative">
                    <div className="absolute -left-[7px] top-1.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-brand-dark-blue"></div>
                    <div className='flex-1'>
                       <p className="font-semibold text-gray-400 flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-cyan-400/70" />
                          {/* Show the exact scheduled date */}
                          {formatDate(msg.scheduled_at)}
                       </p>
                       <p className="text-gray-200 mt-1 italic bg-black/20 p-2 rounded-md">"{msg.content}"</p>
                    </div>
                  </li>
                )
              })}
            </ul>

            {/* --- FIX: Only show buttons for DRAFT plans --- */}
            {plan.status === 'DRAFT' && (
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
            )}
          </div>
        )}
      </InfoCard>
    </>
  );
};