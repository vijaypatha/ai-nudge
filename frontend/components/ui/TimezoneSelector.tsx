// frontend/components/ui/TimezoneSelector.tsx
// Enhanced timezone selector with automatic detection

'use client';

import React, { useEffect, useState } from 'react';
import { getTimezoneOptions, detectUserTimezone, getTimezoneLabel } from '@/utils/timezone';

interface TimezoneSelectorProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
  className?: string;
  autoDetect?: boolean; // Whether to auto-detect user's timezone
  showCurrentTime?: boolean; // Whether to show current time in timezone
}

export const TimezoneSelector: React.FC<TimezoneSelectorProps> = ({ 
  value, 
  onChange, 
  disabled, 
  className,
  autoDetect = true,
  showCurrentTime = false
}) => {
  const [detectedTimezone, setDetectedTimezone] = useState<string>('');
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    if (autoDetect && !value) {
      const detected = detectUserTimezone();
      setDetectedTimezone(detected);
      // Auto-select the detected timezone
      onChange({ target: { value: detected } } as React.ChangeEvent<HTMLSelectElement>);
    }
  }, [autoDetect, value, onChange]);

  useEffect(() => {
    if (showCurrentTime && value) {
      const updateTime = () => {
        try {
          const now = new Date();
          const formatter = new Intl.DateTimeFormat('en-US', {
            timeZone: value,
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          });
          setCurrentTime(formatter.format(now));
        } catch (error) {
          setCurrentTime('');
        }
      };
      
      updateTime();
      const interval = setInterval(updateTime, 60000); // Update every minute
      return () => clearInterval(interval);
    }
  }, [showCurrentTime, value]);

  const timezoneOptions = getTimezoneOptions();

  return (
    <div className="relative">
      <select
        name="timezone"
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={className || "w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white disabled:opacity-50"}
      >
        <option value="">Select a timezone...</option>
        {timezoneOptions.map(tz => (
          <option key={tz.value} value={tz.value}>
            {tz.label}
          </option>
        ))}
      </select>
      {showCurrentTime && currentTime && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400 pointer-events-none">
          {currentTime}
        </div>
      )}
    </div>
  );
};