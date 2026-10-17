'use client';

import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, BookOpen, CheckCircle2, Clock3, Plus, Search, Sparkles, X } from 'lucide-react';

type Lead = { id: string; name: string; interest: string; source: string };
type Course = { id: string; title: string; category: string; description: string; topics: string[]; interests: string[]; fee: string; duration: string };
type Booking = { id: string; leadId: string; startsAt: string; status: 'Pending' | 'Cancelled'; note: string };
type FollowUp = { id: string; leadId: string; title: string; dueAt: string; priority: 'High' | 'Medium' | 'Low'; status: 'Pending' | 'Completed' };
type DemoStore = { bookings: Booking[]; followUps: FollowUp[] };

const STORAGE_KEY = 'lead-desk-demo-workflows-v1';
const leads: Lead[] = [
  { id: 'LD-1048', name: 'Rohan Sharma', interest: 'Data science, statistics and Python', source: 'WhatsApp' },
  { id: 'LD-1047', name: 'Priya Patel', interest: 'Full-stack development and programming', source: 'Instagram' },
  { id: 'LD-1046', name: 'Aarav Singh', interest: 'AI, machine learning and experiments', source: 'Website' },
  { id: 'LD-1045', name: 'Sneha Kulkarni', interest: 'UI/UX design, visual research and creativity', source: 'Walk-in' },
  { id: 'LD-1044', name: 'Kabir Deshmukh', interest: 'Web development and building apps', source: 'WhatsApp' },
  { id: 'LD-1043', name: 'Meera Joshi', interest: 'Cloud, automation and deployment', source: 'Phone' },
];
const courses: Course[] = [
  { id: 'DEMO-DATA-101', title: 'Data Science with Python', category: 'Analytics', description: 'An illustrative introduction to data analysis, statistics and visualisation.', topics: ['Python fundamentals', 'Pandas and data cleaning', 'Statistics basics', 'Data visualisation'], interests: ['data', 'statistics', 'python', 'analytics', 'numbers'], fee: 'Not verified', duration: 'Not verified' },
  { id: 'DEMO-WEB-101', title: 'Full-Stack Web Development', category: 'Software', description: 'Explore responsive interfaces, APIs, databases and web application delivery.', topics: ['HTML and CSS', 'JavaScript and React', 'API integration', 'SQL and deployment'], interests: ['web', 'development', 'programming', 'software', 'apps', 'coding'], fee: 'Not verified', duration: 'Not verified' },
  { id: 'DEMO-AI-101', title: 'AI & Machine Learning Foundations', category: 'Artificial Intelligence', description: 'Understand AI concepts, model evaluation and responsible AI use.', topics: ['AI and ML concepts', 'Data preparation', 'Model evaluation', 'Responsible AI'], interests: ['ai', 'machine learning', 'experiments', 'model', 'algorithm'], fee: 'Not verified', duration: 'Not verified' },
  { id: 'DEMO-UX-101', title: 'UI/UX Design Fundamentals', category: 'Design', description: 'Learn user research, interaction flows, prototypes and usability testing.', topics: ['User research', 'Wireframes', 'Prototyping', 'Accessibility'], interests: ['design', 'visual', 'creative', 'user experience', 'research', 'ux'], fee: 'Not verified', duration: 'Not verified' },
  { id: 'DEMO-CLOUD-101', title: 'Cloud & DevOps Essentials', category: 'Cloud', description: 'Explore deployment workflows, automation and infrastructure basics.', topics: ['Cloud concepts', 'CI/CD basics', 'Deployment', 'Monitoring'], interests: ['cloud', 'automation', 'deployment', 'devops', 'infrastructure'], fee: 'Not verified', duration: 'Not verified' },
];

function dateOffset(days: number, hour = 11) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  date.setHours(hour, 0, 0, 0);
  return date.toISOString();
}
function initialStore(): DemoStore {
  return {
    bookings: [
      { id: 'DEMO-BK-001', leadId: 'LD-1044', startsAt: dateOffset(1, 11), status: 'Pending', note: 'Web development overview' },
      { id: 'DEMO-BK-002', leadId: 'LD-1048', startsAt: dateOffset(2, 14), status: 'Pending', note: 'Data science curriculum walkthrough' },
      { id: 'DEMO-BK-003', leadId: 'LD-1047', startsAt: dateOffset(3, 12), status: 'Pending', note: 'Full-stack course Q&A' },
      { id: 'DEMO-BK-004', leadId: 'LD-1045', startsAt: dateOffset(-1, 15), status: 'Cancelled', note: 'Portfolio and design track' },
    ],
    followUps: [
      { id: 'DEMO-FU-001', leadId: 'LD-1048', title: 'Call to discuss Data Science curriculum', dueAt: dateOffset(0, 14), priority: 'High', status: 'Pending' },
      { id: 'DEMO-FU-002', leadId: 'LD-1047', title: 'Send Full-Stack syllabus', dueAt: dateOffset(0, 16), priority: 'Medium', status: 'Pending' },
      { id: 'DEMO-FU-003', leadId: 'LD-1046', title: 'Share AI foundations overview', dueAt: dateOffset(1, 10), priority: 'Medium', status: 'Pending' },
      { id: 'DEMO-FU-004', leadId: 'LD-1045', title: 'Discuss portfolio expectations', dueAt: dateOffset(2, 11), priority: 'Low', status: 'Pending' },
      { id: 'DEMO-FU-005', leadId: 'LD-1044', title: 'Confirm demo agenda', dueAt: dateOffset(0, 12), priority: 'High', status: 'Completed' },
      { id: 'DEMO-FU-006', leadId: 'LD-1043', title: 'Introduce Cloud & DevOps track', dueAt: dateOffset(3, 15), priority: 'Low', status: 'Pending' },
    ],
  };
}
function formatDate(value: string) {
  return new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata' });
}
function leadName(id: string) { return leads.find(lead => lead.id === id)?.name || 'Unknown demo lead'; }
function Panel({ title, children, extra }: { title: string; children: React.ReactNode; extra?: React.ReactNode }) {
  return <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]"><div className="flex items-center justify-between gap-3 border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">{title}</h2>{extra}</div><div className="p-5">{children}</div></section>;
}
function Tag({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-raised)] px-2.5 py-1 text-[10px] font-semibold text-[var(--color-muted)]">{children}</span>;
}

export default function DemoWorkflowSections({ section }: { section: 'courses' | 'bookings' | 'followups' }) {
  const [store, setStore] = useState<DemoStore>(() => initialStore());
  const [ready, setReady] = useState(false);
  const [leadFilter, setLeadFilter] = useState('LD-1048');
  const [query, setQuery] = useState('');
  const [bookingLead, setBookingLead] = useState('LD-1044');
  const [bookingDate, setBookingDate] = useState(() => dateOffset(1).slice(0, 10));
  const [bookingTime, setBookingTime] = useState('11:00');
  const [bookingNote, setBookingNote] = useState('Course introduction and questions');
  const [taskLead, setTaskLead] = useState('LD-1048');
  const [taskTitle, setTaskTitle] = useState('Call to discuss course options');
  const [taskDue, setTaskDue] = useState(() => dateOffset(1).slice(0, 16));
  const [taskPriority, setTaskPriority] = useState<FollowUp['priority']>('Medium');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as Partial<DemoStore>;
        setStore({ bookings: Array.isArray(parsed.bookings) ? parsed.bookings : initialStore().bookings, followUps: Array.isArray(parsed.followUps) ? parsed.followUps : initialStore().followUps });
      }
    } catch { /* Keep safe in-memory demo defaults when storage is unavailable. */ }
    setReady(true);
  }, []);
  useEffect(() => {
    if (!ready) return;
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store)); } catch { /* Storage may be disabled; the demo still works in memory. */ }
  }, [ready, store]);

  const recommended = useMemo(() => {
    const lead = leads.find(item => item.id === leadFilter) || leads[0];
    const text = lead.interest.toLowerCase();
    return courses.map(course => {
      const matches = course.interests.filter(keyword => text.includes(keyword.toLowerCase()));
      const score = matches.length ? Math.min(96, Math.round(55 + matches.length * 13)) : 0;
      return { course, score, matches };
    }).filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .filter(item => (item.course.title + ' ' + item.course.category + ' ' + item.course.description).toLowerCase().includes(query.toLowerCase()));
  }, [leadFilter, query]);

  function addBooking(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const startsAt = new Date(bookingDate + 'T' + bookingTime + ':00+05:30');
    if (Number.isNaN(startsAt.getTime()) || startsAt <= new Date()) { setNotice('Choose a valid future date and time.'); return; }
    const booking: Booking = { id: 'DEMO-BK-' + Date.now().toString().slice(-7), leadId: bookingLead, startsAt: startsAt.toISOString(), status: 'Pending', note: bookingNote.trim() || 'Demo session' };
    setStore(previous => ({ ...previous, bookings: [booking, ...previous.bookings] }));
    setNotice('Demo booking added locally. No calendar event was created or confirmed.');
  }
  function addTask(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!taskTitle.trim()) return;
    const dueAt = new Date(taskDue);
    if (Number.isNaN(dueAt.getTime())) { setNotice('Choose a valid due date and time.'); return; }
    const task: FollowUp = { id: 'DEMO-FU-' + Date.now().toString().slice(-7), leadId: taskLead, title: taskTitle.trim(), dueAt: dueAt.toISOString(), priority: taskPriority, status: 'Pending' };
    setStore(previous => ({ ...previous, followUps: [task, ...previous.followUps] }));
    setTaskTitle('');
    setNotice('Demo follow-up saved locally. No message or reminder was sent.');
  }

  const banner = <div className="mb-5 flex items-start gap-3 rounded-xl border border-[var(--color-warning)] bg-[var(--color-warning-soft)] px-4 py-3 text-xs leading-5 text-[var(--color-warning)]"><Sparkles size={15} className="mt-0.5 shrink-0"/> <span><strong>Demo data only.</strong> Records are illustrative and saved in this browser. They are not persisted to Supabase, do not confirm calendar availability, and do not send messages.</span></div>;

  if (section === 'courses') return <div className="space-y-5">{banner}<div className="grid gap-4 sm:grid-cols-3">{[['Demo leads', String(leads.length), 'Sample enquiries'], ['Course options', String(courses.length), 'Illustrative catalogue'], ['Recommendations', String(recommended.length), 'Interest keyword matches']].map(([label, value, hint]) => <div key={label} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"><p className="text-xs text-[var(--color-muted)]">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p><p className="mt-1 text-[11px] text-[var(--color-subtle)]">{hint}</p></div>)}</div><Panel title="Course recommendations" extra={<Tag>Heuristic demo</Tag>}><div className="mb-4 grid gap-3 sm:grid-cols-[1fr_1fr]"><label className="text-xs font-semibold">Select demo lead<select value={leadFilter} onChange={e=>setLeadFilter(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs">{leads.map(lead=><option key={lead.id} value={lead.id}>{lead.name} — {lead.interest}</option>)}</select></label><label className="text-xs font-semibold">Filter courses<span className="relative mt-2 block"><Search size={14} className="absolute left-3 top-3 text-[var(--color-subtle)]"/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search course or category" className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] py-2.5 pl-9 pr-3 text-xs"/></span></label></div><p className="mb-4 text-xs text-[var(--color-muted)]">Interest profile: {leads.find(lead=>lead.id===leadFilter)?.interest}. Scores are illustrative keyword similarity, not model confidence or admission probability.</p><div className="grid gap-3 lg:grid-cols-2">{recommended.map(({course,score,matches})=><article key={course.id} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-raised)] p-4"><div className="flex items-start justify-between gap-3"><div><Tag>{course.category}</Tag><h3 className="mt-3 text-sm font-bold">{course.title}</h3></div><span className="rounded-lg bg-[var(--color-accent-soft)] px-3 py-2 text-xs font-bold text-[var(--color-accent)]">{score}% match</span></div><p className="mt-2 text-xs leading-5 text-[var(--color-muted)]">{course.description}</p><p className="mt-3 text-[11px] font-semibold">Matched interests: <span className="font-normal text-[var(--color-muted)]">{matches.join(', ')}</span></p><ul className="mt-3 flex flex-wrap gap-2">{course.topics.map(topic=><li key={topic}><Tag>{topic}</Tag></li>)}</ul><div className="mt-4 grid grid-cols-2 gap-2 border-t border-[var(--color-border)] pt-3 text-[11px]"><p><span className="text-[var(--color-subtle)]">Fee</span><br/><strong>{course.fee}</strong></p><p><span className="text-[var(--color-subtle)]">Duration</span><br/><strong>{course.duration}</strong></p></div></article>)}</div>{recommended.length===0&&<p className="py-8 text-center text-xs text-[var(--color-muted)]">No sample courses match this filter.</p>}</Panel></div>;

  if (section === 'bookings') return <div className="space-y-5">{banner}<div className="grid gap-4 sm:grid-cols-3">{[['Total demo bookings', String(store.bookings.length), 'Local sample records'], ['Pending', String(store.bookings.filter(item=>item.status==='Pending').length), 'Not calendar-confirmed'], ['Cancelled', String(store.bookings.filter(item=>item.status==='Cancelled').length), 'Sample records']].map(([label,value,hint])=><div key={label} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"><p className="text-xs text-[var(--color-muted)]">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p><p className="mt-1 text-[11px] text-[var(--color-subtle)]">{hint}</p></div>)}</div><div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]"><Panel title="Demo booking schedule"><div className="space-y-3">{[...store.bookings].sort((a,b)=>a.startsAt.localeCompare(b.startsAt)).map(booking=><div key={booking.id} className="flex flex-col gap-3 rounded-xl border border-[var(--color-border)] p-4 sm:flex-row sm:items-center"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--color-accent-soft)] text-[var(--color-accent)]"><CalendarDays size={18}/></div><div className="min-w-0 flex-1"><p className="text-xs font-bold">{leadName(booking.leadId)}</p><p className="mt-1 text-xs text-[var(--color-muted)]">{booking.note}</p><p className="mt-1 text-[10px] text-[var(--color-subtle)]">{formatDate(booking.startsAt)} · {booking.id}</p></div><div className="flex items-center gap-2"><Tag>{booking.status}</Tag>{booking.status==='Pending'&&<button onClick={()=>setStore(previous=>({...previous,bookings:previous.bookings.map(item=>item.id===booking.id?{...item,status:'Cancelled'}:item)}))} className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-[10px] font-semibold hover:bg-[var(--color-raised)]">Cancel</button>}</div></div>)}</div></Panel><Panel title="Add a demo booking"><form onSubmit={addBooking} className="space-y-4"><label className="block text-xs font-semibold">Lead<select value={bookingLead} onChange={e=>setBookingLead(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs">{leads.map(lead=><option key={lead.id} value={lead.id}>{lead.name}</option>)}</select></label><label className="block text-xs font-semibold">Date<input required type="date" min={new Date().toISOString().slice(0,10)} value={bookingDate} onChange={e=>setBookingDate(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"/></label><label className="block text-xs font-semibold">Time (India)<input required type="time" value={bookingTime} onChange={e=>setBookingTime(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"/></label><label className="block text-xs font-semibold">Session note<input value={bookingNote} onChange={e=>setBookingNote(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"/></label><button className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white"><Plus size={14}/> Add demo booking</button></form></Panel></div></div>;

  return <div className="space-y-5">{banner}<div className="grid gap-4 sm:grid-cols-3">{[['Total follow-ups', String(store.followUps.length), 'Local sample tasks'], ['Pending', String(store.followUps.filter(item=>item.status==='Pending').length), 'Not automatically sent'], ['Completed', String(store.followUps.filter(item=>item.status==='Completed').length), 'Demo status only']].map(([label,value,hint])=><div key={label} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"><p className="text-xs text-[var(--color-muted)]">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p><p className="mt-1 text-[11px] text-[var(--color-subtle)]">{hint}</p></div>)}</div><div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]"><Panel title="Follow-up queue"><div className="space-y-3">{[...store.followUps].sort((a,b)=>a.dueAt.localeCompare(b.dueAt)).map(task=><div key={task.id} className="flex flex-col gap-3 rounded-xl border border-[var(--color-border)] p-4 sm:flex-row sm:items-center"><button onClick={()=>setStore(previous=>({...previous,followUps:previous.followUps.map(item=>item.id===task.id?{...item,status:item.status==='Completed'?'Pending':'Completed'}:item)}))} aria-label={task.status==='Completed'?'Reopen task':'Complete task'} className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${task.status==='Completed'?'border-emerald-500 bg-emerald-500/10 text-emerald-500':'border-[var(--color-border)] text-[var(--color-muted)]'}`}><CheckCircle2 size={16}/></button><div className="min-w-0 flex-1"><p className={`text-xs font-bold ${task.status==='Completed'?'line-through text-[var(--color-subtle)]':''}`}>{task.title}</p><p className="mt-1 text-xs text-[var(--color-muted)]">{leadName(task.leadId)}</p><p className="mt-1 flex items-center gap-1 text-[10px] text-[var(--color-subtle)]"><Clock3 size={12}/>{formatDate(task.dueAt)}</p></div><div className="flex items-center gap-2"><Tag>{task.priority} priority</Tag><Tag>{task.status}</Tag></div></div>)}</div></Panel><Panel title="Create a demo follow-up"><form onSubmit={addTask} className="space-y-4"><label className="block text-xs font-semibold">Lead<select value={taskLead} onChange={e=>setTaskLead(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs">{leads.map(lead=><option key={lead.id} value={lead.id}>{lead.name}</option>)}</select></label><label className="block text-xs font-semibold">Task title<input required value={taskTitle} onChange={e=>setTaskTitle(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"/></label><label className="block text-xs font-semibold">Due date/time<input required type="datetime-local" value={taskDue} onChange={e=>setTaskDue(e.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"/></label><label className="block text-xs font-semibold">Priority<select value={taskPriority} onChange={e=>setTaskPriority(e.target.value as FollowUp['priority'])} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"><option>High</option><option>Medium</option><option>Low</option></select></label><button className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white"><Plus size={14}/> Save demo follow-up</button></form></Panel></div></div>;
}
