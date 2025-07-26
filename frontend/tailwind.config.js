// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': 'var(--color-background, #0B112B)',
        'brand-text-main': 'var(--color-text, #E5E7EB)',
        'brand-text-muted': 'var(--color-text-muted, #9CA3AF)',
        'primary-action': 'var(--color-action, #22d3ee)',
        'brand-accent': 'var(--color-accent, #22d3ee)',
        'brand-primary': '#191C36',
        'brand-secondary': 'var(--color-action, #22d3ee)',
        'brand-white': '#FFFFFF',
        'brand-gray': '#C4C4C4',
        'theme-primary-from': 'var(--color-primary-from, #22d3ee)',
        'theme-primary-to': 'var(--color-primary-to, #3b82f6)',
        'theme-accent': 'var(--color-accent, #22d3ee)',
        'theme-action': 'var(--color-action, #22d3ee)',
        'theme-success': 'var(--color-success, #10b981)',
        'theme-warning': 'var(--color-warning, #f59e0b)',
        'theme-error': 'var(--color-error, #ef4444)',
        'theme-background': 'var(--color-background, #0B112B)',
        'theme-surface': 'var(--color-surface, #1e293b)',
        'theme-text': 'var(--color-text, #E5E7EB)',
        'theme-text-muted': 'var(--color-text-muted, #9CA3AF)',
        'theme-border': 'var(--color-border, #374151)',
      },
      // --- MODIFIED: Added keyframes and animation utilities ---
      keyframes: {
        'gradient-animation': {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        'text-shine': {
          'to': { backgroundPosition: '200% center' },
        }
      },
      animation: {
        'gradient-animation': 'gradient-animation 30s ease infinite',
        'text-shine': 'text-shine 5s linear infinite',
      },
    },
  },
  plugins: [],
};