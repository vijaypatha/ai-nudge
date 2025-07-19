// frontend/components/ui/TagFilter.tsx
// --- NEW FILE ---
// Purpose: A reusable component to display and select tags for filtering client lists.

'use client';

import { useState } from 'react';
import { Tag } from 'lucide-react';

interface TagFilterProps {
    // A list of all unique tags available for filtering.
    allTags: string[];
    // A callback function that is invoked when the tag selection changes.
    onFilterChange: (selectedTags: string[]) => void;
}

/**
 * Renders a set of clickable tag "pills" that allows a user to select
 * multiple tags to apply as a filter.
 */
export const TagFilter = ({ allTags, onFilterChange }: TagFilterProps) => {
    // State to track the currently selected tags.
    const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());

    /**
     * Toggles the selection state of a given tag and calls the parent
     * component's onFilterChange callback with the new list of selected tags.
     * @param tag The string identifier of the tag to toggle.
     */
    const toggleTag = (tag: string) => {
        const newSelectedTags = new Set(selectedTags);
        if (newSelectedTags.has(tag)) {
            newSelectedTags.delete(tag);
        } else {
            newSelectedTags.add(tag);
        }
        setSelectedTags(newSelectedTags);
        // Inform the parent component of the change.
        onFilterChange(Array.from(newSelectedTags));
    };

    if (allTags.length === 0) {
        return null; // Don't render the component if there are no tags to show.
    }

    return (
        <div className="bg-white/5 p-4 rounded-lg mb-6">
            <h3 className="text-sm font-semibold text-brand-text-muted mb-3 flex items-center gap-2">
                <Tag size={16} />
                Filter by Tags
            </h3>
            <div className="flex flex-wrap gap-2">
                {allTags.map((tag) => (
                    <button
                        key={tag}
                        onClick={() => toggleTag(tag)}
                        className={`px-3 py-1 text-xs font-semibold rounded-full transition-colors duration-200 ease-in-out ${
                            selectedTags.has(tag)
                                ? 'bg-primary-action text-brand-dark shadow-md'
                                : 'bg-white/10 hover:bg-white/20 text-brand-text-main'
                        }`}
                    >
                        {tag}
                    </button>
                ))}
            </div>
        </div>
    );
};
