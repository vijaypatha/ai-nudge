/** @type {import('next').NextConfig} */
module.exports = {
    content: [
      './pages/**/*.{js,ts,jsx,tsx,mdx}',
      './components/**/*.{js,ts,jsx,tsx,mdx}',
      './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
      extend: {
        // Define your application's brand color palette here
        colors: {
          brand: {
            dark: '#0B112B', // Deep, dark blue from your background
            'accent': '#20D5B3',      // The vibrant teal/mint green
            'accent-light': '#4EDAA8', // The lighter green for gradients
            'text-main': '#FFFFFF',
            'text-muted': '#C4C4C4',
          },
          // We can also define component-specific colors for a clean system
          "primary-action": "#20D5B3",
        },
      },
    },
    plugins: [],
  };