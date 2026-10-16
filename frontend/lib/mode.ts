export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== 'false';
export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '') + '/api/v1';
export const DEFAULT_TIMEZONE = process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE || 'Asia/Kolkata';
