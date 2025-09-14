import Link from 'next/link';
import { MessageSquare, Edit } from 'lucide-react';
import { SurveyTemplate } from '@/app/(main)/surveys/page';

interface SurveyCardProps {
  template: SurveyTemplate;
}

export const SurveyCard = ({ template }: SurveyCardProps) => {
  return (
    <div className="bg-brand-primary border border-white/10 rounded-xl flex flex-col group hover:border-cyan-400/50 transition-all duration-300 transform hover:-translate-y-1">
      <div className="p-5 flex-grow">
        <h3 className="font-bold text-lg text-white mb-2 truncate">{template.name}</h3>
        <p className="text-sm text-gray-400 mb-4 h-10 line-clamp-2">{template.description || 'No description provided.'}</p>
      </div>
      <div className="flex justify-between items-center p-4 border-t border-white/10 bg-black/10 rounded-b-xl">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <MessageSquare size={14} />
          <span>{template.questions?.length || 0} Questions</span>
        </div>
        <Link 
          href={`/surveys/${template.id}`} 
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-md text-xs font-semibold text-white hover:bg-cyan-500 hover:text-brand-dark transition-colors"
        >
          <Edit size={12} />
          Edit
        </Link>
      </div>
    </div>
  );
};
