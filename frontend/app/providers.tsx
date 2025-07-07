// frontend/app/providers.tsx
// DEFINITIVE FIX: Wraps all children with the SidebarProvider so the layout
// and its pages can share sidebar state.

'use client';

import { AppProvider } from '@/context/AppContext';
import { SidebarProvider } from '@/context/SidebarContext'; // Import the provider

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AppProvider>
      {/* SidebarProvider now wraps the children, making the context available */}
      <SidebarProvider>
        {children}
      </SidebarProvider>
    </AppProvider>
  );
}