// frontend/utils/timezone.ts
// Timezone detection and conversion utilities for seamless scheduling

export interface TimezoneInfo {
  value: string;
  label: string;
  offset: string;
}

// Common timezones with proper labels
export const TIMEZONES: TimezoneInfo[] = [
  { value: 'America/New_York', label: 'Eastern Time (ET)', offset: 'UTC-5' },
  { value: 'America/Chicago', label: 'Central Time (CT)', offset: 'UTC-6' },
  { value: 'America/Denver', label: 'Mountain Time (MT)', offset: 'UTC-7' },
  { value: 'America/Phoenix', label: 'Mountain Time (no DST)', offset: 'UTC-7' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)', offset: 'UTC-8' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)', offset: 'UTC-9' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)', offset: 'UTC-10' },
  { value: 'Europe/London', label: 'Greenwich Mean Time (GMT)', offset: 'UTC+0' },
  { value: 'Europe/Paris', label: 'Central European Time (CET)', offset: 'UTC+1' },
  { value: 'Asia/Tokyo', label: 'Japan Standard Time (JST)', offset: 'UTC+9' },
  { value: 'Asia/Shanghai', label: 'China Standard Time (CST)', offset: 'UTC+8' },
  { value: 'Australia/Sydney', label: 'Australian Eastern Time (AET)', offset: 'UTC+10' },
];

/**
 * Detects the user's current timezone automatically
 */
export function detectUserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    console.warn('Failed to detect timezone, falling back to UTC:', error);
    return 'UTC';
  }
}

/**
 * Gets a user-friendly timezone label
 */
export function getTimezoneLabel(timezone: string): string {
  const tz = TIMEZONES.find(t => t.value === timezone);
  if (tz) return tz.label;
  
  // For unknown timezones, format them nicely
  try {
    const date = new Date();
    const formatter = new Intl.DateTimeFormat('en', {
      timeZone: timezone,
      timeZoneName: 'long'
    });
    return formatter.formatToParts(date).find(part => part.type === 'timeZoneName')?.value || timezone;
  } catch {
    return timezone;
  }
}

/**
 * Converts a local datetime string to a specific timezone
 */
export function convertToTimezone(localDateTime: string, targetTimezone: string): string {
  try {
    const date = new Date(localDateTime);
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: targetTimezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    
    return formatter.format(date).replace(',', '');
  } catch (error) {
    console.error('Timezone conversion failed:', error);
    return localDateTime;
  }
}

/**
 * Converts a datetime from one timezone to another
 */
export function convertBetweenTimezones(
  dateTime: string, 
  fromTimezone: string, 
  toTimezone: string
): string {
  try {
    // Create a date object in the source timezone
    const date = new Date(dateTime);
    
    // Format it in the target timezone
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: toTimezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    
    return formatter.format(date).replace(',', '');
  } catch (error) {
    console.error('Timezone conversion failed:', error);
    return dateTime;
  }
}

/**
 * Gets the current time in a specific timezone as a datetime-local string
 */
export function getCurrentTimeInTimezone(timezone: string): string {
  try {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    
    return formatter.format(now).replace(',', '');
  } catch (error) {
    console.error('Failed to get current time in timezone:', error);
    return new Date().toISOString().slice(0, 16);
  }
}

/**
 * Gets a future time (default 30 minutes) in a specific timezone
 */
export function getFutureTimeInTimezone(
  timezone: string, 
  minutesFromNow: number = 30
): string {
  try {
    const future = new Date(Date.now() + minutesFromNow * 60 * 1000);
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    
    return formatter.format(future).replace(',', '');
  } catch (error) {
    console.error('Failed to get future time in timezone:', error);
    const future = new Date(Date.now() + minutesFromNow * 60 * 1000);
    return future.toISOString().slice(0, 16);
  }
}

/**
 * Validates if a timezone string is valid
 */
export function isValidTimezone(timezone: string): boolean {
  try {
    Intl.DateTimeFormat(undefined, { timeZone: timezone });
    return true;
  } catch {
    return false;
  }
}

/**
 * Gets timezone options for a select dropdown
 */
export function getTimezoneOptions(): { value: string; label: string }[] {
  return TIMEZONES.map(tz => ({
    value: tz.value,
    label: `${tz.label} (${tz.offset})`
  }));
} 