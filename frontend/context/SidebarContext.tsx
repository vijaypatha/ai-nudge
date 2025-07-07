// frontend/context/SidebarContext.tsx
// DEFINITIVE: This file creates the state management for the sidebar.
'use client';

import { createContext, useState, ReactNode, useContext, Dispatch, SetStateAction } from 'react';

// Define the shape of the context's data
interface SidebarContextProps {
    isSidebarOpen: boolean;
    setIsSidebarOpen: Dispatch<SetStateAction<boolean>>;
}

// Create the context. It's undefined by default until the Provider gives it a value.
const SidebarContext = createContext<SidebarContextProps | undefined>(undefined);

// Create the custom hook that our components will use to access the sidebar state.
// This hook also ensures a component is wrapped in the provider, preventing errors.
export const useSidebar = () => {
    const context = useContext(SidebarContext);
    if (context === undefined) {
        throw new Error('useSidebar must be used within a SidebarProvider');
    }
    return context;
};

// Create the Provider component. This component will wrap our layout.
export const SidebarProvider = ({ children }: { children: ReactNode }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    return (
        <SidebarContext.Provider value={{ isSidebarOpen, setIsSidebarOpen }}>
            {children}
        </SidebarContext.Provider>
    );
};