import { NextResponse } from 'next/server';

export async function POST() {
  const response = NextResponse.json({ signed_out: true });
  response.cookies.set('lead-desk-session', '', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/', maxAge: 0 });
  response.cookies.set('lead-desk-refresh', '', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/', maxAge: 0 });
  return response;
}
