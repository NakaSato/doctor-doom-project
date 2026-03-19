/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Design Token System for Doctor Doom
      colors: {
        // Primary - Solar/Energy theme
        primary: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b', // Solar yellow
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        // Secondary - Tech/Professional
        secondary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6', // Professional blue
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Thermal palette for heat maps
        thermal: {
          cold: '#0000ff',
          cool: '#00ffff',
          neutral: '#00ff00',
          warm: '#ffff00',
          hot: '#ff0000',
        },
        // Severity colors
        severity: {
          low: '#22c55e',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#ef4444',
        },
        // Status colors
        status: {
          success: '#22c55e',
          warning: '#f59e0b',
          error: '#ef4444',
          info: '#3b82f6',
        },
      },
      // Typography
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      // Spacing for consistent layouts
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      // Border radius
      borderRadius: {
        '4xl': '2rem',
      },
      // Shadows for depth
      boxShadow: {
        'glow': '0 0 20px rgba(245, 158, 11, 0.3)',
        'glow-lg': '0 0 40px rgba(245, 158, 11, 0.4)',
      },
      // Animations
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-slow': 'bounce 2s infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      // Z-index layers
      zIndex: {
        '-1': '-1',
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
      // Aspect ratios
      aspectRatio: {
        '4/3': '4 / 3',
        'thermal': '640 / 512',
      },
    },
  },
  plugins: [],
};
