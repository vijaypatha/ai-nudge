// frontend/components/ui/Avatar.tsx
// --- FINAL VERSION ---
// This version correctly generates colors based on the name and renders the avatar.

import React from 'react';

interface AvatarProps {
  name: string;
  imageUrl?: string | null;
  className?: string;
}

// A simple function to generate a color based on the name's characters
// This ensures the same user always gets the same color.
const generateColor = (name: string) => {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash;
  }
  const color = `hsl(${hash % 360}, 50%, 70%)`;
  const textColor = `hsl(${hash % 360}, 100%, 20%)`;
  return { backgroundColor: color, color: textColor };
};

export const Avatar: React.FC<AvatarProps> = ({ name, imageUrl, className = '' }) => {
  const getInitials = (name: string) => {
    if (!name) return '?';
    const names = name.trim().split(' ');
    if (names.length > 1) {
      return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
    }
    return names[0].substring(0, 2).toUpperCase();
  };

  if (imageUrl) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={imageUrl} alt={name} className={`rounded-full object-cover ${className}`} />;
  }

  const { backgroundColor, color } = generateColor(name);
  const initials = getInitials(name);

  return (
    <div
      className={`rounded-full flex items-center justify-center font-bold ${className}`}
      style={{ backgroundColor, color }}
    >
      {initials}
    </div>
  );
};