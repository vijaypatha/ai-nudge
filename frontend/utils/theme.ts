// frontend/utils/theme.ts
// Centralized theme configuration for easy color scheme management

export interface ThemeColors {
  primary: {
    from: string;
    to: string;
  };
  accent: string;
  action: string;
  success: string;
  warning: string;
  error: string;
  // Dark/Light theme colors
  background: string;
  surface: string;
  text: string;
  textMuted: string;
  border: string;
}

// Blue Theme - Dark (Default)
export const BLUE_DARK_THEME: ThemeColors = {
  primary: {
    from: '#22d3ee', // cyan-400
    to: '#3b82f6',   // blue-500
  },
  accent: '#22d3ee', // cyan-400
  action: '#22d3ee', // cyan-400
  success: '#10b981', // emerald-500
  warning: '#f59e0b', // amber-500
  error: '#ef4444',   // red-500
  background: '#0B112B', // brand-dark
  surface: '#1e293b', // slate-800
  text: '#E5E7EB', // brand-text-main
  textMuted: '#9CA3AF', // brand-text-muted
  border: '#374151', // gray-700
};

// Green Theme - Dark
export const GREEN_DARK_THEME: ThemeColors = {
  primary: {
    from: '#10b981', // emerald-500
    to: '#059669',   // emerald-600
  },
  accent: '#10b981', // emerald-500
  action: '#10b981', // emerald-500
  success: '#10b981', // emerald-500
  warning: '#f59e0b', // amber-500
  error: '#ef4444',   // red-500
  background: '#0B112B', // brand-dark
  surface: '#1e293b', // slate-800
  text: '#E5E7EB', // brand-text-main
  textMuted: '#9CA3AF', // brand-text-muted
  border: '#374151', // gray-700
};

// Active theme - Blue Dark is default (current setting)
export const ACTIVE_THEME = BLUE_DARK_THEME;

// Utility functions for generating CSS classes
export const getGradientClass = () => `bg-gradient-to-r from-[${ACTIVE_THEME.primary.from}] to-[${ACTIVE_THEME.primary.to}]`;
export const getAccentClass = () => `text-[${ACTIVE_THEME.accent}]`;
export const getActionClass = () => `bg-[${ACTIVE_THEME.action}]`;
export const getSuccessClass = () => `text-[${ACTIVE_THEME.success}]`;
export const getWarningClass = () => `text-[${ACTIVE_THEME.warning}]`;
export const getErrorClass = () => `text-[${ACTIVE_THEME.error}]`;

// CSS Variables for Tailwind
export const getThemeCSSVariables = () => ({
  '--color-primary-from': ACTIVE_THEME.primary.from,
  '--color-primary-to': ACTIVE_THEME.primary.to,
  '--color-accent': ACTIVE_THEME.accent,
  '--color-action': ACTIVE_THEME.action,
  '--color-success': ACTIVE_THEME.success,
  '--color-warning': ACTIVE_THEME.warning,
  '--color-error': ACTIVE_THEME.error,
  '--color-background': ACTIVE_THEME.background,
  '--color-surface': ACTIVE_THEME.surface,
  '--color-text': ACTIVE_THEME.text,
  '--color-text-muted': ACTIVE_THEME.textMuted,
  '--color-border': ACTIVE_THEME.border,
}); 