export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== 'false';

// Route browser requests through Next.js so the backend URL stays server-side
// and the frontend does not depend on cross-origin CORS configuration.
const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '/backend-api';
export const API_BASE_URL = configuredApiBase.startsWith('http')
  ? '/backend-api'
  : configuredApiBase.replace(/\/$/, '');

export const DEFAULT_TIMEZONE =
  process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE || 'Asia/Kolkata';
