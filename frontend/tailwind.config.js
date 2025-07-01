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
        // --- CORE THEME ---
        'brand-dark': '#0B112B', // Deep, dark blue for backgrounds
        'brand-text-main': '#E5E7EB', // Off-white for primary text
        'brand-text-muted': '#9CA3AF', // Gray for secondary/muted text

        // --- ACTION & ACCENT COLORS ---
        'primary-action': '#20D5B3', // Bright teal for primary buttons/actions
        'brand-accent': '#4EDAA8',   // Lighter green for highlights and secondary elements

        // --- Original colors for reference, can be removed if unused ---
        'brand-primary': '#191C36',
        'brand-secondary': '#20D5B3',
        'brand-white': '#FFFFFF',
        'brand-gray': '#C4C4C4',
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      // --- ADD THIS ---
      animation: {
        'aurora': 'aurora 60s linear infinite',
      },
      keyframes: {
        aurora: {
          from: {
            backgroundPosition: '0% 50%',
          },
          to: {
            backgroundPosition: '200% 50%',
          },
        },
      },
      // --- END ADD ---
    },
  },
  plugins: [],
};