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
        'brand-dark': '#0B112B',
        'brand-text-main': '#E5E7EB',
        'brand-text-muted': '#9CA3AF',
        'primary-action': '#20D5B3',
        'brand-accent': '#4EDAA8',
        'brand-primary': '#191C36',
        'brand-secondary': '#20D5B3',
        'brand-white': '#FFFFFF',
        'brand-gray': '#C4C4C4',
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