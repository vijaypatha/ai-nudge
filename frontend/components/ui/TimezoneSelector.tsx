// frontend/components/ui/TimezoneSelector.tsx
// --- NEW FILE ---

'use client';

import React from 'react';

const timezones = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Phoenix', label: 'Mountain Time (no DST)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
];

interface TimezoneSelectorProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
  className?: string;
}

export const TimezoneSelector: React.FC<TimezoneSelectorProps> = ({ value, onChange, disabled, className }) => {
  return (
    <select
      name="timezone"
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={className || "w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50"}
    >
      <option value="">Select a timezone...</option>
      {timezones.map(tz => (
        <option key={tz.value} value={tz.value}>{tz.label}</option>
      ))}
    </select>
  );
};