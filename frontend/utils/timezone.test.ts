// frontend/utils/timezone.test.ts
// Simple tests for timezone utilities

import { 
    detectUserTimezone, 
    getTimezoneLabel, 
    convertToTimezone, 
    getCurrentTimeInTimezone,
    getFutureTimeInTimezone,
    isValidTimezone,
    getTimezoneOptions 
} from './timezone';

// Mock the browser's Intl API for testing
const mockIntl = {
    DateTimeFormat: jest.fn().mockReturnValue({
        resolvedOptions: () => ({ timeZone: 'America/New_York' }),
        format: () => '2024-01-01 12:00',
        formatToParts: () => [{ type: 'timeZoneName', value: 'Eastern Time' }]
    })
};

// Mock the global Intl object
Object.defineProperty(global, 'Intl', {
    value: mockIntl,
    writable: true
});

describe('Timezone Utilities', () => {
    test('detectUserTimezone should return a valid timezone', () => {
        const timezone = detectUserTimezone();
        expect(timezone).toBe('America/New_York');
    });

    test('getTimezoneLabel should return user-friendly labels', () => {
        expect(getTimezoneLabel('America/New_York')).toBe('Eastern Time (ET)');
        expect(getTimezoneLabel('America/Los_Angeles')).toBe('Pacific Time (PT)');
        expect(getTimezoneLabel('Unknown/Timezone')).toBe('Unknown/Timezone');
    });

    test('isValidTimezone should validate timezones correctly', () => {
        expect(isValidTimezone('America/New_York')).toBe(true);
        expect(isValidTimezone('Invalid/Timezone')).toBe(false);
    });

    test('getTimezoneOptions should return formatted options', () => {
        const options = getTimezoneOptions();
        expect(options).toHaveLength(12); // Number of timezones in our list
        expect(options[0]).toHaveProperty('value');
        expect(options[0]).toHaveProperty('label');
        expect(options[0].label).toContain('(');
    });

    test('getCurrentTimeInTimezone should return formatted time', () => {
        const time = getCurrentTimeInTimezone('America/New_York');
        expect(typeof time).toBe('string');
        expect(time).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
    });

    test('getFutureTimeInTimezone should return future time', () => {
        const time = getFutureTimeInTimezone('America/New_York', 30);
        expect(typeof time).toBe('string');
        expect(time).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
    });

    test('convertToTimezone should handle timezone conversion', () => {
        const localTime = '2024-01-01T12:00';
        const converted = convertToTimezone(localTime, 'America/Los_Angeles');
        expect(typeof converted).toBe('string');
        expect(converted).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
    });
}); 