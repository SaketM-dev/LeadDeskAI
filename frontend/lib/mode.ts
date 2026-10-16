export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== 'false';

// Browser requests go through a same-origin Next.js rewrite. The backend URL stays
// server-side so the browser does not need CORS access to the FastAPI host.
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || '/backend-api'
).replace(/\/$/, '');

export const DEFAULT_TIMEZONE =
  process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE || 'Asia/Kolkata';
