import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!supabaseUrl || !anonKey) {
    return NextResponse.json({ message: 'Supabase sign-in is not configured on the server.' }, { status: 503 });
  }

  let credentials: { email?: string; password?: string };
  try { credentials = await request.json(); }
  catch { return NextResponse.json({ message: 'Enter your email and password.' }, { status: 400 }); }
  if (!credentials.email || !credentials.password) {
    return NextResponse.json({ message: 'Enter your email and password.' }, { status: 400 });
  }

  let authResponse: Response;
  try {
    authResponse = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
      method: 'POST',
      headers: { apikey: anonKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: credentials.email, password: credentials.password }),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ message: 'Supabase sign-in is temporarily unavailable.' }, { status: 503 });
  }
  if (!authResponse.ok) {
    return NextResponse.json({ message: 'Email or password is incorrect.' }, { status: 401 });
  }
  const session = await authResponse.json() as { access_token?: string; refresh_token?: string; expires_in?: number };
  if (!session.access_token || !session.refresh_token) return NextResponse.json({ message: 'Supabase did not return a session.' }, { status: 502 });

  const response = NextResponse.json({ signed_in: true });
  const options = {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
  };
  response.cookies.set('lead-desk-session', session.access_token, { ...options, maxAge: Math.max(60, Math.min(session.expires_in ?? 3600, 3600)) });
  response.cookies.set('lead-desk-refresh', session.refresh_token, { ...options, maxAge: 60 * 60 * 24 * 30 });
  return response;
}
