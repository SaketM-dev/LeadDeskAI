import { API_BASE_URL, DEMO_MODE } from './mode';

export class ApiRequestError extends Error {
  constructor(message: string, public status: number, public code?: string) { super(message); this.name = 'ApiRequestError'; }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (DEMO_MODE) throw new Error('Live API calls are disabled while demo mode is active.');
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...init.headers },
    });
  } catch {
    throw new ApiRequestError('The API could not be reached. Check the backend URL and network.', 0, 'NETWORK_ERROR');
  }
  if (!response.ok) {
    let message = `API request failed (${response.status})`;
    let code: string | undefined;
    try { const body = await response.json(); message = body?.error?.message || message; code = body?.error?.code; } catch { /* non-JSON error body */ }
    throw new ApiRequestError(message, response.status, code);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
