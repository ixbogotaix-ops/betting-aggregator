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
        dark: '#0a0f1d',
        darker: '#060912',
        card: '#0f172a',
        accent: '#3b82f6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        cyber: {
          blue: '#2563eb',
          cyan: '#06b6d4',
          gold: '#eab308',
          purple: '#8b5cf6',
          emerald: '#10b981'
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-gold': 'glowGold 2.5s ease-in-out infinite alternate',
        'radar': 'radarPing 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      keyframes: {
        glowGold: {
          '0%': { boxShadow: '0 0 15px rgba(245, 158, 11, 0.2), inset 0 0 15px rgba(245, 158, 11, 0.1)' },
          '100%': { boxShadow: '0 0 30px rgba(245, 158, 11, 0.45), inset 0 0 25px rgba(245, 158, 11, 0.2)' }
        },
        radarPing: {
          '75%, 100%': {
            transform: 'scale(2.2)',
            opacity: '0',
          },
        }
      }
    },
  },
  plugins: [],
}
