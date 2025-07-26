// frontend/components/ThemeSwitcher.tsx
// Theme switcher component for easy color scheme changes

'use client';

import { useState } from 'react';
import { 
  BLUE_DARK_THEME, 
  GREEN_DARK_THEME, 
  getThemeCSSVariables 
} from '@/utils/theme';
import { Moon } from 'lucide-react';

interface ThemeSwitcherProps {
  className?: string;
}

export function ThemeSwitcher({ className = '' }: ThemeSwitcherProps) {
  const [currentTheme, setCurrentTheme] = useState<'blue-dark' | 'green-dark'>('blue-dark');

  const themes = {
    'blue-dark': { name: 'Blue Dark', theme: BLUE_DARK_THEME, icon: Moon },
    'green-dark': { name: 'Green Dark', theme: GREEN_DARK_THEME, icon: Moon },
  };

  const applyTheme = (themeName: 'blue-dark' | 'green-dark') => {
    const theme = themes[themeName].theme;
    const root = document.documentElement;
    const themeVariables = {
      '--color-primary-from': theme.primary.from,
      '--color-primary-to': theme.primary.to,
      '--color-accent': theme.accent,
      '--color-action': theme.action,
      '--color-success': theme.success,
      '--color-warning': theme.warning,
      '--color-error': theme.error,
      '--color-background': theme.background,
      '--color-surface': theme.surface,
      '--color-text': theme.text,
      '--color-text-muted': theme.textMuted,
      '--color-border': theme.border,
    };
    
    Object.entries(themeVariables).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });
    
    setCurrentTheme(themeName);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex gap-2">
        {Object.entries(themes).map(([key, { name, theme, icon: Icon }]) => (
          <button
            key={key}
            onClick={() => applyTheme(key as 'blue-dark' | 'green-dark')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              currentTheme === key
                ? 'bg-white/10 text-white border border-white/20'
                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
            }`}
          >
            <Icon className="w-4 h-4" />
            <div 
              className="w-3 h-3 rounded-full"
              style={{ 
                background: `linear-gradient(45deg, ${theme.primary.from}, ${theme.primary.to})` 
              }}
            />
            <span className="hidden sm:inline">{name}</span>
          </button>
        ))}
      </div>
      
      <div className="text-xs text-gray-500">
        <p>💡 <strong>Blue Dark</strong> is the default theme (current branding)</p>
        <p>🌙 Both themes maintain the dark UI aesthetic</p>
        <p>🎨 Choose between blue or green branding colors</p>
      </div>
    </div>
  );
} 