// frontend/components/ui/Avatar.tsx
// Purpose: A reusable component to display a user's initials as a styled avatar.
// Consistent styling for avatars across the application.

import clsx from 'clsx';

/**
 * Props for the Avatar component.
 * @param name - The full name of the user to generate initials from.
 * @param className - Optional additional classes for styling.
 */
interface AvatarProps {
  name: string;
  className?: string;
}

/**
 * Renders a circular avatar with the user's initials.
 * Handles name splitting and capitalization.
 */
export const Avatar = ({ name, className }: AvatarProps) => {
  // Generates initials from the user's name.
  // Example: "John Doe" -> "JD"
  const initials = name?.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() || '';

  return (
    <div className={clsx(
      "flex items-center justify-center rounded-full bg-white/10 text-brand-text-muted font-bold select-none",
      className
    )}>
      {initials}
    </div>
  );
};