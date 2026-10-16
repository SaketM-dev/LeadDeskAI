import { Activity, CalendarCheck, GraduationCap, Users } from 'lucide-react';
import { DEMO_MODE, API_BASE_URL, DEFAULT_TIMEZONE } from '@/lib/mode';

const metrics = [
  { label: 'Total leads', value: '128', icon: Users, note: 'Sample dashboard metric' },
  { label: 'Follow-ups due', value: '12', icon: Activity, note: 'Fictional demo data' },
  { label: 'Demo bookings', value: '8', icon: CalendarCheck, note: 'Simulated bookings' },
  { label: 'Course interests', value: '4', icon: GraduationCap, note: 'Sample courses only' },
];
const leads = [
  { name: 'Aarav Sharma', interest: 'Full-Stack Web Development', stage: 'Qualified', score: 78 },
  { name: 'Meera Joshi', interest: 'Data Analytics with Python', stage: 'Contacted', score: 64 },
  { name: 'Kabir Deshmukh', interest: 'AI & Machine Learning Foundations', stage: 'New', score: 52 },
];

export default function HomePage() {
  return <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <header className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
      <div><p className="text-sm font-semibold text-brand-600">ADMISSIONS OPERATIONS</p><h1 className="mt-1 text-3xl font-bold tracking-tight">AI Lead Desk</h1><p className="mt-2 text-sm text-slate-500">Manage enquiries, counselor activity and next steps from one workspace.</p></div>
      <span className={`w-fit rounded-full px-3 py-1.5 text-xs font-semibold ${DEMO_MODE ? 'bg-purple-100 text-purple-800' : 'bg-emerald-100 text-emerald-800'}`}>{DEMO_MODE ? 'DEMO DATA' : 'LIVE API MODE'}</span>
    </header>
    <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Summary metrics">{metrics.map(({ label, value, icon: Icon, note }) => <article key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><p className="text-sm text-slate-500">{label}</p><Icon size={19} className="text-brand-600" aria-hidden="true" /></div><p className="mt-3 text-3xl font-bold">{value}</p><p className="mt-1 text-xs text-slate-500">{note}</p></article>)}</section>
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-5 py-4"><h2 className="font-semibold">Priority leads</h2><p className="mt-1 text-sm text-slate-500">Illustrative records for the Phase 1 foundation.</p></div><div className="overflow-x-auto"><table className="w-full min-w-[620px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">Prospect</th><th className="px-5 py-3">Course interest</th><th className="px-5 py-3">Stage</th><th className="px-5 py-3">Lead score</th></tr></thead><tbody className="divide-y divide-slate-100">{leads.map(lead => <tr key={lead.name}><td className="px-5 py-4 font-medium">{lead.name}</td><td className="px-5 py-4 text-slate-600">{lead.interest}</td><td className="px-5 py-4"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs">{lead.stage}</span></td><td className="px-5 py-4 font-semibold">{lead.score}<span className="ml-1 text-xs font-normal text-slate-400">/100</span></td></tr>)}</tbody></table></div></section>
    <section className="mt-6 grid gap-4 md:grid-cols-2"><article className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Environment</h2><dl className="mt-3 space-y-2 text-sm"><div className="flex justify-between gap-4"><dt className="text-slate-500">API base</dt><dd className="truncate font-mono text-xs">{API_BASE_URL}</dd></div><div className="flex justify-between"><dt className="text-slate-500">Display timezone</dt><dd>{DEFAULT_TIMEZONE}</dd></div></dl></article><article className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Next implementation stages</h2><p className="mt-2 text-sm leading-6 text-slate-600">Leads and timeline, AI counselling inbox, aptitude assessment, demo booking, follow-up queue, analytics, knowledge base and settings will be implemented in subsequent phases.</p></article></section>
  </main>;
}
