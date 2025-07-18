// FILE: frontend/components/profile/Content_Discovery.tsx

'use client';

import { useState, FC } from 'react';
import { X } from 'lucide-react';

interface ContentDiscoveryProps {
  // This component receives the current list of specialties
  initialSpecialties: string[];
  // It calls back with the complete new list whenever a change is made
  onSpecialtiesChange: (specialties: string[]) => void;
}

export const ContentDiscovery: FC<ContentDiscoveryProps> = ({ initialSpecialties, onSpecialtiesChange }) => {
    const [currentSpecialty, setCurrentSpecialty] = useState('');

    const handleAddSpecialty = () => {
        const newSpecialty = currentSpecialty.trim().toLowerCase();
        // Check for duplicates and empty strings
        if (newSpecialty && !initialSpecialties.includes(newSpecialty)) {
            const updatedSpecialties = [...initialSpecialties, newSpecialty];
            onSpecialtiesChange(updatedSpecialties); // Inform the parent of the new list
            setCurrentSpecialty(''); // Clear the input
        }
    };

    const handleRemoveSpecialty = (specialtyToRemove: string) => {
        const updatedSpecialties = initialSpecialties.filter(s => s !== specialtyToRemove);
        onSpecialtiesChange(updatedSpecialties); // Inform the parent of the new list
    };

    return (
        <div className="space-y-4">
            <label className="text-sm font-medium text-gray-400">
                AI Content Discovery Topics
            </label>
            <p className="text-xs text-gray-500 -mt-2">
                Add your specialties (e.g., "anxiety", "parenting") to help your AI find relevant articles and videos for your clients.
            </p>
            <div className="flex flex-wrap items-center gap-2 p-3 bg-white/5 rounded-lg border border-white/10">
                {initialSpecialties.map(specialty => (
                    <span key={specialty} className="flex items-center gap-1.5 bg-sky-500/20 text-sky-300 text-sm font-semibold pl-3 pr-1.5 py-1 rounded-full">
                        {specialty}
                        <button onClick={() => handleRemoveSpecialty(specialty)} className="bg-black/20 hover:bg-black/40 rounded-full p-0.5"><X size={12} /></button>
                    </span>
                ))}
                <input
                    value={currentSpecialty}
                    onChange={(e) => setCurrentSpecialty(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddSpecialty(); } }}
                    placeholder={initialSpecialties.length === 0 ? "Add a specialty..." : "+ Add more"}
                    className="flex-1 bg-transparent focus:outline-none min-w-[120px] text-white"
                />
            </div>
        </div>
    );
};