// frontend/app/providers.tsx
//Purpose: To create a single Client Component that wraps all shared context providers, making them available to all client-side pages and components in the application.


'use client';

import { AppProvider } from '../context/AppContext';
import { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AppProvider>
      {children}
    </AppProvider>
  );
}