// frontend/components/conversation/RelationshipCampaignCard.tsx

'use client';

import { useState } from 'react';
import { Zap, Sparkles, Calendar, Edit2, Loader2, Check, X, PauseCircle, BrainCircuit } from 'lucide-react';
import { useAppContext, ScheduledMessage, CampaignBriefing } from '@/context/AppContext';
import { InfoCard } from '../ui/InfoCard';
import { EditMessageModal } from './EditMessageModal';

interface RelationshipCampaignCardProps {
  plan: CampaignBriefing | null;
  messages: ScheduledMessage[];
  onApprovePlan: (planId: string) => void;
  onDismissPlan: (planId: string) => void;
  isProcessing: boolean;
}

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
        {!hasContent && (
          <div className="text-center py-4">
            <p className="text-sm text-gray-400 mb-3">No campaign planned for this client.</p>
            <button className="w-full bg-green-600/20 text-green-300 text-sm font-semibold py-2 rounded-md hover:bg-green-600/30 transition-colors">
              + Plan Relationship Campaign
            </button>
          </div>
        )}
        
        {plan && plan.is_plan && plan.status.toUpperCase() === 'DRAFT' && (
          <div className="animate-fade-in">
            <h3 className="font-semibold text-white mb-3">{plan.headline}</h3>
            <ul className="space-y-3 pl-1 border-l border-gray-700 ml-1">
              {plan.key_intel.steps?.map((step: any, index: number) => (
                <li key={index} className="text-sm text-gray-300 flex items-start gap-3 pl-4 relative">
                   <div className="absolute -left-[7px] top-1.5 w-3.5 h-3.5 bg-gray-700 rounded-full border-2 border-brand-dark-blue"></div>
                  <div className='flex-1'>
                    <p className="font-semibold text-gray-400">Day {step.delay_days}</p>
                    <p className="text-gray-200 mt-1 italic bg-black/20 p-2 rounded-md">"{step.generated_draft || 'Generating draft...'}"</p>
                  </div>
                </li>
              ))}
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

        {messages.length > 0 && (
          <div className={plan && plan.is_plan ? 'mt-4 pt-4 border-t border-gray-700' : ''}>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Scheduled Messages</h4>
            <ul className="space-y-1">
              {messages.map(msg => (
                <li key={msg.id} onClick={() => setEditingMessage(msg)} className="group flex items-center justify-between hover:bg-white/5 -mx-2 px-2 py-1.5 rounded-md cursor-pointer transition-all">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-4 w-4 text-cyan-400" />
                    <span className="text-sm text-gray-300 truncate">{msg.content}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">{new Date(msg.scheduled_at).toLocaleDateString()}</span>
                    <Edit2 className="h-3 w-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </InfoCard>
    </>
  );
};