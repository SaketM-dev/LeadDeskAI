import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!supabaseUrl || !anonKey) return NextResponse.json({ message: 'Supabase sign-in is not configured on the server.' }, { status: 503 });
  let email: string;
  try { email = String((await request.json()).email ?? '').trim(); }
  catch { return NextResponse.json({ message: 'Enter your email address.' }, { status: 400 }); }
  if (!email) return NextResponse.json({ message: 'Enter your email address.' }, { status: 400 });
  try {
    const response = await fetch(`${supabaseUrl}/auth/v1/recover`, {
      method: 'POST', headers: { apikey: anonKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }), cache: 'no-store',
    });
    if (!response.ok) return NextResponse.json({ message: 'Password reset could not be requested.' }, { status: 502 });
  } catch { return NextResponse.json({ message: 'Supabase sign-in is temporarily unavailable.' }, { status: 503 }); }
  return NextResponse.json({ sent: true });
}
