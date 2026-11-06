import { NextRequest, NextResponse } from 'next/server';

type RouteContext = { params: { path: string[] } };

async function proxy(request: NextRequest, context: RouteContext) {
  const backendUrl = process.env.BACKEND_API_URL?.replace(/\/$/, '');
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!backendUrl) return NextResponse.json({ detail: 'Backend API is not configured.' }, { status: 503 });

  const path = context.params.path.join('/');
  const isHealth = path === 'health' || path.startsWith('health/');
  const isPublicChat = path === 'chatbot/chat' || path === 'chatbot/status';
  let session = request.cookies.get('lead-desk-session')?.value;
  let refreshToken = request.cookies.get('lead-desk-refresh')?.value;
  let refreshed: { access_token: string; refresh_token: string; expires_in: number } | undefined;

  async function refreshSession() {
    if (!refreshToken || !supabaseUrl || !anonKey) return false;
    try {
      const response = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=refresh_token`, {
        method: 'POST',
        headers: { apikey: anonKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: 'no-store',
      });
      if (!response.ok) return false;
      const payload = await response.json() as { access_token?: string; refresh_token?: string; expires_in?: number };
      if (!payload.access_token || !payload.refresh_token) return false;
      refreshed = { access_token: payload.access_token, refresh_token: payload.refresh_token, expires_in: payload.expires_in ?? 3600 };
      session = payload.access_token;
      refreshToken = payload.refresh_token;
      return true;
    } catch { return false; }
  }

  if (!isHealth && !isPublicChat && !session && refreshToken) await refreshSession();
  if (!isHealth && !isPublicChat && !session) {
    return NextResponse.json({ detail: 'Sign in is required.' }, { status: 401 });
  }

  const targetPath = isHealth ? `/${path}` : `/api/${path}`;
  const headers = new Headers({ Accept: request.headers.get('accept') ?? 'application/json' });
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('Content-Type', contentType);
  const body = ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer();

  try {
    const send = async () => {
      if (session) headers.set('Authorization', `Bearer ${session}`);
      return fetch(`${backendUrl}${targetPath}${request.nextUrl.search}`, {
        method: request.method, headers, body, cache: 'no-store',
      });
    };
    let upstream = await send();
    if (upstream.status === 401 && refreshToken && await refreshSession()) upstream = await send();

    const responseHeaders = new Headers();
    for (const name of ['content-type', 'cache-control']) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    responseHeaders.set('Cache-Control', 'no-store');
    const response = new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
    const cookieOptions = { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax' as const, path: '/' };
    if (refreshed) {
      response.cookies.set('lead-desk-session', refreshed.access_token, { ...cookieOptions, maxAge: Math.max(60, Math.min(refreshed.expires_in, 3600)) });
      response.cookies.set('lead-desk-refresh', refreshed.refresh_token, { ...cookieOptions, maxAge: 60 * 60 * 24 * 30 });
    } else if (upstream.status === 401) {
      response.cookies.set('lead-desk-session', '', { ...cookieOptions, maxAge: 0 });
      response.cookies.set('lead-desk-refresh', '', { ...cookieOptions, maxAge: 0 });
    }
    return response;
  } catch {
    return NextResponse.json({ detail: 'The backend API could not be reached.' }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
