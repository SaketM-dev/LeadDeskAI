'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useMemo, useState } from 'react';
import {
  Activity, BarChart3, BookOpen, CalendarDays, ChevronDown, GraduationCap,
  LayoutDashboard, ListTodo, LogOut, Menu, MessageSquare, Search, Settings,
  ShieldCheck, Sparkles, Users, X, BrainCircuit
} from 'lucide-react';

const navigation = [
  { label: 'Overview', href: '/', icon: LayoutDashboard, group: 'WORKSPACE' },
  { label: 'Leads', href: '/leads', icon: Users, group: 'WORKSPACE' },
  { label: 'AI counselling', href: '/inbox', icon: MessageSquare, group: 'WORKSPACE' },
  { label: 'Aptitude assessment', href: '/aptitude', icon: BrainCircuit, group: 'WORKSPACE' },
  { label: 'Course recommendations', href: '/courses', icon: GraduationCap, group: 'WORKSPACE' },
  { label: 'Demo bookings', href: '/bookings', icon: CalendarDays, group: 'WORKSPACE' },
  { label: 'Follow-ups', href: '/followups', icon: ListTodo, group: 'WORKSPACE' },
  { label: 'Analytics', href: '/analytics', icon: BarChart3, group: 'INSIGHTS' },
  { label: 'Knowledge base', href: '/knowledge', icon: BookOpen, group: 'ADMINISTRATION' },
  { label: 'Integrations', href: '/integrations', icon: Activity, group: 'ADMINISTRATION' },
  { label: 'Settings & access', href: '/settings', icon: Settings, group: 'ADMINISTRATION' },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState('');
  const grouped = useMemo(() => navigation.filter(item => item.label.toLowerCase().includes(search.toLowerCase())), [search]);

  return <div className="min-h-screen bg-slate-50 text-slate-900">
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-[76px] items-center gap-3 border-b border-slate-100 px-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm"><Sparkles size={21}/></div>
        <div><div className="font-bold tracking-tight">AI Lead Desk</div><div className="text-[11px] text-slate-500">Admissions workspace</div></div>
        <button onClick={() => setMobileOpen(false)} className="ml-auto rounded-lg p-1 text-slate-500 lg:hidden" aria-label="Close navigation"><X size={19}/></button>
      </div>
      <div className="px-3 pt-4"><label className="relative block"><Search size={15} className="absolute left-3 top-2.5 text-slate-400"/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Find a section" className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"/></label></div>
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {['WORKSPACE','INSIGHTS','ADMINISTRATION'].map(group => {
          const items = grouped.filter(item => item.group === group);
          if (!items.length) return null;
          return <div key={group} className="mb-5"><p className="mb-2 px-3 text-[10px] font-bold tracking-[0.16em] text-slate-400">{group}</p>
            {items.map(item => { const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href); const Icon = item.icon; return <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} className={`mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition ${active ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`}><Icon size={17}/><span>{item.label}</span>{active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-600"/>}</Link>; })}
          </div>;
        })}
      </nav>
      <div className="border-t border-slate-100 p-3"><div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">AC</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">Admissions Counselor</p><p className="text-[10px] text-slate-500">Demo workspace</p></div><ChevronDown size={15} className="text-slate-400"/></div></div>
    </aside>
    {mobileOpen && <button className="fixed inset-0 z-30 bg-slate-950/30 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu overlay"/>}
    <div className="lg:pl-64">
      <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-7">
        <div className="flex items-center gap-3"><button onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" aria-label="Open navigation"><Menu size={20}/></button><div className="hidden text-sm text-slate-400 sm:block">Workspace <span className="mx-2">/</span><span className="font-medium text-slate-700">{navigation.find(n => n.href === pathname)?.label || (pathname === '/' ? 'Overview' : pathname.split('/')[1]?.replace(/-/g,' '))}</span></div></div>
        <div className="flex items-center gap-3"><span className="hidden items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-2.5 py-1 text-[11px] font-semibold text-purple-700 sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-purple-500"/>DEMO MODE</span><div className="hidden h-7 w-px bg-slate-200 sm:block"/><button className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-50"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">AC</div><span className="hidden text-left sm:block"><span className="block text-xs font-semibold">Counselor</span><span className="block text-[10px] text-slate-500">Administrator</span></span><ChevronDown size={14} className="text-slate-400"/></button></div>
      </header>
      <div className="border-b border-purple-200 bg-purple-50 px-4 py-2 text-center text-[11px] font-medium text-purple-800 sm:text-xs">Demo environment — prospect records, course details, messages and bookings shown here are illustrative. No real messages or bookings are sent.</div>
      <main className="mx-auto max-w-[1500px] px-4 py-7 sm:px-7 lg:px-9">{children}</main>
      <footer className="px-7 pb-6 text-center text-[10px] text-slate-400">AI Lead Desk · Phase 1 frontend · Verify backend and provider integrations before live use.</footer>
    </div>
  </div>;
}
