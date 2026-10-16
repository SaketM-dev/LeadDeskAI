import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#eef2ff', 100: '#e0e7ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' },
        surface: { subtle: '#f8fafc' },
        demo: { bg: '#f3e8ff', border: '#d8b4fe', text: '#6b21a8', dot: '#9333ea' }
      },
      boxShadow: { soft: '0 1px 3px rgba(15, 23, 42, 0.06)' }
    }
  },
  plugins: []
};
export default config;
