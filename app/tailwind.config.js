/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  corePlugins: {
    preflight: false, // Disable preflight to prevent conflicts with Mantine
  },
  theme: {
    extend: {
      fontFamily: {
        sans: ['Work Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'sm': '2px',
        'md': '4px',
        'lg': '6px',
        'xl': '8px',
      },
    },
  },
  plugins: [],
} 