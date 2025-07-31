// frontend/components/ui/InfoCard.tsx
// Purpose: A styled container card for displaying information sections.
// Used for "Client Intel", "Relationship Campaign", etc.

import clsx from 'clsx';
import { Edit2 } from 'lucide-react';

/**
 * Props for the InfoCard component.
 * @param title - The title of the card.
 * @param icon - An optional icon to display next to the title.
 * @param children - The content to be rendered inside the card.
 * @param className - Optional additional classes for the card container.
 * @param onEdit - An optional callback function to handle edit actions. If provided, an edit icon is shown.
 */
interface InfoCardProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  onEdit?: () => void;
  isPulsing?: boolean; // New prop for pulsing effect
}

export const InfoCard = ({ title, icon, children, className, onEdit, isPulsing }: InfoCardProps) => (
  <div className={clsx("bg-white/5 border border-white/10 rounded-xl relative transition-all", className)}>
    <div className="flex justify-between items-center px-4 pt-4 pb-2">
      <h3 className="text-sm font-semibold text-brand-text-muted flex items-center gap-2">
        <span className={clsx(isPulsing && "animate-pulse text-cyan-400")}>
            {icon}
        </span>
        {title}
      </h3>
      {onEdit && (
        <button
          onClick={onEdit}
          className="p-1 text-brand-text-muted hover:text-white opacity-50 hover:opacity-100 transition-opacity"
          title="Edit"
        >
          <Edit2 size={14} />
        </button>
      )}
    </div>
    <div className="p-4 pt-0">
      {children}
    </div>
  </div>
);