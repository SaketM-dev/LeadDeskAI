'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useMemo, useState } from 'react';
import { DEMO_MODE } from '@/lib/mode';
import {
  Activity, BarChart3, BookOpen, CalendarDays, ChevronDown, GraduationCap,
  LayoutDashboard, ListTodo, Menu, MessageSquare, Search, Settings,
  Sparkles, Users, X, BrainCircuit
} from 'lucide-react';

const navigation = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard, group: 'WORKSPACE' },
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
  const activeItem = navigation.find(item => item.href === pathname || (item.href !== '/' && pathname.startsWith(item.href)));

  return <div className="min-h-screen bg-[var(--color-page)] text-[var(--color-text)]">
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-transform duration-200 lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-[76px] items-center gap-3 border-b border-[var(--color-border)] px-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-accent-strong)] text-white"><Sparkles size={21}/></div>
        <div><div className="font-bold tracking-tight">AI Lead Desk</div><div className="text-[11px] text-[var(--color-muted)]">Admissions workspace</div></div>
        <button onClick={() => setMobileOpen(false)} className="ml-auto rounded-lg p-1 text-[var(--color-muted)] lg:hidden" aria-label="Close navigation"><X size={19}/></button>
      </div>
      <div className="px-3 pt-4"><label className="relative block"><span className="sr-only">Find a section</span><Search size={15} className="absolute left-3 top-2.5 text-[var(--color-subtle)]"/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Find a section" className="ui-input pl-9 text-xs"/></label></div>
      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Main navigation">
        {['WORKSPACE','INSIGHTS','ADMINISTRATION'].map(group => {
          const items = grouped.filter(item => item.group === group);
          if (!items.length) return null;
          return <div key={group} className="mb-5"><p className="mb-2 px-3 text-[10px] font-bold tracking-[0.16em] text-[var(--color-subtle)]">{group}</p>
            {items.map(item => { const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href); const Icon = item.icon; return <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} aria-current={active ? 'page' : undefined} className={`mb-1 flex items-center gap-3 rounded-lg border px-3 py-2.5 text-[13px] font-medium transition-colors duration-160 ${active ? 'border-[var(--color-border)] bg-[var(--color-accent-soft)] text-[var(--color-accent)]' : 'border-transparent text-[var(--color-muted)] hover:bg-[var(--color-raised)] hover:text-[var(--color-text)]'}`}><Icon size={17}/><span>{item.label}</span>{active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-[var(--color-accent)]"/>}</Link>; })}
          </div>;
        })}
      </nav>
      <div className="border-t border-[var(--color-border)] p-3"><div className="flex items-center gap-3 rounded-xl bg-[var(--color-raised)] p-3"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-accent-soft)] text-xs font-bold text-[var(--color-accent)]">AC</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">Admissions Counselor</p><p className="text-[10px] text-[var(--color-muted)]">Role not authenticated</p></div><ChevronDown size={15} className="text-[var(--color-subtle)]"/></div></div>
    </aside>
    {mobileOpen && <button className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu overlay"/>}
    <div className="lg:pl-64">
      <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-page)]/95 px-4 backdrop-blur sm:px-7">
        <div className="flex items-center gap-3"><button onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-[var(--color-muted)] hover:bg-[var(--color-raised)] lg:hidden" aria-label="Open navigation"><Menu size={20}/></button><div className="hidden text-sm text-[var(--color-muted)] sm:block">Workspace <span className="mx-2">/</span><span className="font-medium capitalize text-[var(--color-text)]">{activeItem?.label || pathname.split('/')[1]?.replace(/-/g,' ') || 'Overview'}</span></div></div>
        <div className="flex items-center gap-3"><span className="ui-badge border-[var(--color-border)] bg-[var(--color-raised)] text-[var(--color-muted)]"><span className={`h-1.5 w-1.5 rounded-full ${DEMO_MODE ? 'bg-[var(--color-purple)]' : 'bg-[var(--color-success)]'}`}/>{DEMO_MODE ? 'Demo data' : 'Live mode'}</span><div className="hidden h-7 w-px bg-[var(--color-border)] sm:block"/><div className="flex items-center gap-2"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-raised)] text-xs font-semibold text-[var(--color-text)]">?</div><span className="hidden text-left sm:block"><span className="block text-xs font-semibold">Workspace user</span><span className="block text-[10px] text-[var(--color-muted)]">Authentication not connected</span></span></div></div>
      </header>
      <div className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-center text-[11px] leading-5 text-[var(--color-muted)] sm:text-xs">{DEMO_MODE ? 'Demo data · Records are fictional; changes may be local only. No real messages or bookings are sent.' : 'Live mode · Only implemented backend endpoints are live. Unsupported actions will report errors instead of saving sample data.'}</div>
      <main className="mx-auto max-w-[1500px] px-4 py-7 sm:px-7 lg:px-9">{children}</main>
      <footer className="px-7 pb-6 text-center text-[10px] text-[var(--color-subtle)]">AI Lead Desk · Verify database, authentication and provider integrations before production use.</footer>
    </div>
  </div>;
}
