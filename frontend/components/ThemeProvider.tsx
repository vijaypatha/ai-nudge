// frontend/components/ThemeProvider.tsx
// Theme provider that applies CSS variables to the entire app

'use client';

import { ReactNode, useEffect } from 'react';
import { ACTIVE_THEME, getThemeCSSVariables } from '@/utils/theme';

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  useEffect(() => {
    // Apply theme CSS variables to the document root
    const root = document.documentElement;
    const themeVariables = getThemeCSSVariables();
    
    Object.entries(themeVariables).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });

    // Cleanup function to remove CSS variables when component unmounts
    return () => {
      Object.keys(themeVariables).forEach((property) => {
        root.style.removeProperty(property);
      });
    };
  }, []);

  return <>{children}</>;
} 