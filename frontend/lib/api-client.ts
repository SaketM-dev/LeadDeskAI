import { API_BASE_URL, DEMO_MODE } from './mode';

export class ApiRequestError extends Error {
  constructor(message: string, public readonly status: number, public readonly code?: string, public readonly requestId?: string) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

type ApiErrorPayload = {
  error?: { code?: string; message?: string; request_id?: string };
  // FastAPI's default HTTPException response uses { detail: ... }.
  detail?: string | { code?: string; message?: string };
  message?: string;
};

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (DEMO_MODE) throw new ApiRequestError('Live API requests are disabled in demo mode.', 0, 'DEMO_MODE');
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...(typeof window !== 'undefined' && window.sessionStorage.getItem('lead-desk-api-token') ? { Authorization: `Bearer ${window.sessionStorage.getItem('lead-desk-api-token')}` } : {}), ...init.headers },
    });
  } catch {
    throw new ApiRequestError('The API could not be reached. Check BACKEND_API_URL and ensure FastAPI is running.', 0, 'NETWORK_ERROR');
  }
  if (!response.ok) {
    let message = `API request failed (${response.status})`;
    let code: string | undefined;
    let requestId: string | undefined;
    try {
      const payload = await response.json() as ApiErrorPayload;
      const detailMessage = typeof payload.detail === 'string'
        ? payload.detail
        : payload.detail?.message;
      message = payload.error?.message || detailMessage || payload.message || message;
      code = payload.error?.code || (typeof payload.detail === 'object' ? payload.detail.code : undefined);
      requestId = payload.error?.request_id;
    } catch { /* Preserve the HTTP status message for non-JSON responses. */ }
    throw new ApiRequestError(message, response.status, code, requestId);
  }
  if (response.status === 204) return undefined as T;
  return await response.json() as T;
}
