# Theme System Guide

## Overview
The app now has a centralized theme system with Dark/Light variants that makes it easy to change the entire color scheme from one place.

## How to Change Themes

### Option 1: Using the Theme Switcher (Easiest)
1. Go to your Profile page (`/profile`)
2. Scroll down to the "App Theme" section
3. Click on any theme button:
   - 🌙 **Blue Dark** (Default) - Current branding
   - 🌙 **Green Dark** - Green branding variant
4. The entire app will instantly change colors

### Option 2: Code Changes (For Developers)

#### To Change the Default Theme:
1. Open `frontend/utils/theme.ts`
2. Find the line: `export const ACTIVE_THEME = BLUE_DARK_THEME;`
3. Change it to:
   - `export const ACTIVE_THEME = GREEN_DARK_THEME;` (Green Dark)

#### To Create a New Theme:
1. In `frontend/utils/theme.ts`, add a new theme object:
```typescript
export const ORANGE_DARK_THEME: ThemeColors = {
  primary: {
    from: '#f97316', // orange-500
    to: '#ea580c',   // orange-600
  },
  accent: '#f97316',
  action: '#f97316',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  background: '#0B112B', // dark background
  surface: '#1e293b',
  text: '#E5E7EB',
  textMuted: '#9CA3AF',
  border: '#374151',
};
```

2. Update the ACTIVE_THEME:
```typescript
export const ACTIVE_THEME = ORANGE_DARK_THEME;
```

## Available Themes

### Blue Dark Theme (Default)
- 🌙 Dark mode with blue branding
- Matches current app design
- Colors: Cyan to Blue gradient on dark background

### Green Dark Theme
- 🌙 Dark mode with green branding
- Professional and growth-oriented
- Colors: Emerald gradient on dark background

## Theme Features

### Dark UI Aesthetic
- Maintains the current dark UI experience
- Same branding colors (blue/green)
- Dark backgrounds and surfaces
- High contrast text
- Professional and modern look

## How It Works

1. **CSS Variables**: The theme system uses CSS custom properties (variables) that are applied to the document root
2. **Tailwind Integration**: Tailwind classes automatically use these variables
3. **Dynamic Changes**: The ThemeSwitcher component updates CSS variables in real-time
4. **Consistent Colors**: All components use the same color variables
5. **Background/Text Adaptation**: Themes include proper background, surface, text, and border colors

## Files Involved

- `frontend/utils/theme.ts` - Theme definitions and utilities
- `frontend/components/ThemeProvider.tsx` - Applies theme to the app
- `frontend/components/ThemeSwitcher.tsx` - UI for switching themes
- `frontend/tailwind.config.js` - Tailwind configuration with theme variables
- `frontend/app/providers.tsx` - Includes ThemeProvider

## Benefits

✅ **Easy to Change**: One click changes the entire app
✅ **Dark UI Focus**: Maintains the professional dark aesthetic
✅ **Consistent Branding**: Maintains brand colors across themes
✅ **Professional**: Proper color theory and accessibility
✅ **Flexible**: Easy to add new themes
✅ **Real-time**: Instant theme switching without page reload
✅ **User Choice**: Users can choose their preferred theme 