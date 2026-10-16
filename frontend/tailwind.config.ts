import type { Config } from 'tailwindcss';

const token = (name: string) => `var(--${name})`;

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: token('color-accent-soft'),
          100: token('color-border'),
          500: token('color-accent'),
          600: token('color-accent-strong'),
          700: token('color-accent'),
        },
        surface: {
          DEFAULT: token('color-surface'),
          subtle: token('color-page'),
          raised: token('color-raised'),
        },
        ink: {
          DEFAULT: token('color-text'),
          muted: token('color-muted'),
          subtle: token('color-subtle'),
        },
        status: {
          success: token('color-success'),
          warning: token('color-warning'),
          danger: token('color-danger'),
          info: token('color-info'),
        },
        demo: {
          bg: token('color-purple-soft'),
          border: token('color-border'),
          text: token('color-purple'),
          dot: token('color-purple'),
        },
      },
      borderRadius: {
        card: 'var(--radius-card)',
        control: 'var(--radius-control)',
      },
      boxShadow: {
        soft: 'var(--shadow-card)',
        raised: 'var(--shadow-raised)',
      },
      transitionDuration: { 160: '160ms', 180: '180ms' },
    },
  },
  plugins: [],
};
export default config;
