'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck, Sparkles } from 'lucide-react';
import { Badge, Button, Input } from '@/components/ui';

async function readMessage(response: Response) {
  const payload = await response.json().catch(() => ({}));
  return typeof payload.message === 'string' ? payload.message : 'The request could not be completed.';
}

export default function LoginPage() {
  const router = useRouter();
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [visible,setVisible]=useState(false);
  const [message,setMessage]=useState('');
  const [busy,setBusy]=useState(false);

  async function submit(event:React.FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      const response = await fetch('/api/auth/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email,password}) });
      if (!response.ok) throw new Error(await readMessage(response));
      const identity = await fetch('/backend-api/v1/auth/me', { cache:'no-store' });
      if (!identity.ok) {
        await fetch('/api/auth/logout', { method:'POST' });
        throw new Error(await readMessage(identity));
      }
      router.replace('/dashboard');
    } catch(error) { setMessage(error instanceof Error ? error.message : 'Sign-in failed.'); }
    finally { setBusy(false); }
  }

  async function resetPassword() {
    setBusy(true); setMessage('');
    try {
      const response = await fetch('/api/auth/forgot-password', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email}) });
      if (!response.ok) throw new Error(await readMessage(response));
      setMessage('If an account exists for that email, Supabase will send password reset instructions.');
    } catch(error) { setMessage(error instanceof Error ? error.message : 'Password reset could not be requested.'); }
    finally { setBusy(false); }
  }

  return <div className="mx-auto grid max-w-5xl overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-raised)] lg:grid-cols-2">
    <div className="flex flex-col justify-between border-b border-[var(--color-border)] bg-[var(--color-page)] p-8 sm:p-10 lg:border-b-0 lg:border-r"><div><Link href="/" aria-label="Back to AI Lead Desk home" className="mb-5 inline-flex items-center gap-3 rounded-xl"><span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-300/15 bg-violet-400/10 text-violet-200"><Sparkles size={23}/></span><span className="text-sm font-semibold tracking-tight text-white">lead<span className="text-violet-300">desk</span><span className="ml-1 rounded border border-white/10 px-1 py-0.5 text-[9px] uppercase tracking-widest text-white/40">AI</span></span></Link><Badge tone="info"><span className="h-1.5 w-1.5 rounded-full bg-[var(--color-info)]"/>Admissions workspace</Badge><h1 className="mt-8 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">Every enquiry.<br/>One clear next step.</h1><p className="mt-4 max-w-sm text-sm leading-6 text-[var(--color-muted)]">Manage prospect enquiries, counselling, course recommendations and follow-ups from one focused workspace.</p></div><div className="mt-12 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"><ShieldCheck size={18} className="text-[var(--color-success)]"/><p className="mt-3 text-sm font-semibold">Staff access is controlled</p><p className="mt-1 text-xs leading-5 text-[var(--color-muted)]">Sign in with an account enabled for this admissions workspace.</p></div></div>
    <div className="p-8 sm:p-10"><div className="mb-8"><h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2><p className="mt-2 text-sm text-[var(--color-muted)]">Sign in with your institute account.</p></div><form onSubmit={submit} className="space-y-5"><label className="block text-sm font-medium" htmlFor="login-email">Email address<span className="relative mt-2 block"><Mail size={16} className="absolute left-3 top-3 text-[var(--color-subtle)]"/><Input id="login-email" type="email" autoComplete="username" required value={email} onChange={e=>setEmail(e.target.value)} className="pl-10" placeholder="you@institute.com"/></span></label><label className="block text-sm font-medium" htmlFor="login-password">Password<span className="relative mt-2 block"><LockKeyhole size={16} className="absolute left-3 top-3 text-[var(--color-subtle)]"/><Input id="login-password" type={visible?'text':'password'} autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} className="pr-10 pl-10" placeholder="Enter password"/><button type="button" onClick={()=>setVisible(v=>!v)} className="absolute right-3 top-3 text-[var(--color-muted)]" aria-label={visible?'Hide password':'Show password'}>{visible?<EyeOff size={16}/>:<Eye size={16}/>}</button></span></label><div className="flex justify-end"><button type="button" disabled={busy} onClick={resetPassword} className="text-xs font-semibold text-[var(--color-accent)] hover:underline">Forgot password?</button></div><Button type="submit" disabled={busy} className="w-full">{busy?'Signing in…':'Sign in'}</Button></form>{message&&<p role="status" className="mt-4 rounded-xl border border-[var(--color-warning)]/40 bg-[var(--color-warning-soft)] p-3 text-xs leading-5 text-[var(--color-warning)]">{message}</p>}<p className="mt-6 text-center text-[11px] leading-5 text-[var(--color-muted)]">Accounts are created by a workspace administrator. Supabase verifies passwords; this app checks your staff role before opening the workspace.</p></div>
  </div>;
}
