// frontend/components/ui/Tabs.tsx
// Purpose: A reusable, consistent tab component for the entire application.
// This ensures that all tab groups have the same look, feel, and behavior.

'use client';

import clsx from 'clsx';

/**
 * Represents a single tab option.
 * @param id - A unique identifier for the tab.
 * @param label - The text to display on the tab.
 */
export interface TabOption {
    id: string;
    label: string;
}

/**
 * Props for the Tabs component.
 * @param options - An array of TabOption objects to render.
 * @param activeTab - The ID of the currently active tab.
 * @param setActiveTab - A callback function to set the active tab when one is clicked.
 * @param className - Optional additional classes for the container.
 */
interface TabsProps {
    options: TabOption[];
    activeTab: string;
    setActiveTab: (id: string) => void;
    className?: string;
}

/**
 * Renders a stylized, consistent tab group.
 * The style is based on the "Nudges" page segmented control.
 */
export const Tabs = ({ options, activeTab, setActiveTab, className }: TabsProps) => {
    return (
        <div className={clsx(
            "bg-brand-primary p-1 rounded-lg flex items-center gap-1 self-stretch sm:self-auto border border-white/10",
            className
        )}>
            {options.map((option) => (
                <button
                    key={option.id}
                    onClick={() => setActiveTab(option.id)}
                    className={clsx(
                        "px-4 py-1.5 text-sm font-semibold rounded-md flex-1 sm:flex-none transition-colors duration-200",
                        activeTab === option.id
                            ? 'bg-white/10 text-white'
                            : 'text-brand-text-muted hover:bg-white/5'
                    )}
                >
                    {option.label}
                </button>
            ))}
        </div>
    );
};
