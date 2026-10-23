/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        heading: ['"Montserrat"', '"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        dark: '#0f172a',
        darker: '#0b1120',
        card: '#1e293b',
        accent: '#3b82f6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444'
      }
    },
  },
  plugins: [],
}
