'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, Clock3, Plus, Sparkles } from 'lucide-react';

type Task = {
  id: string;
  lead: string;
  title: string;
  due: string;
  priority: 'High' | 'Medium' | 'Low';
  status: 'Pending' | 'Completed';
};

const KEY = 'lead-desk-demo-followups-v2';
const seed: Task[] = [
  { id: 'FU-DEMO-001', lead: 'Rohan Sharma', title: 'Call to discuss Data Science curriculum', due: '2026-10-17T14:30', priority: 'High', status: 'Pending' },
  { id: 'FU-DEMO-002', lead: 'Priya Patel', title: 'Send Full-Stack course syllabus', due: '2026-10-17T16:00', priority: 'Medium', status: 'Pending' },
  { id: 'FU-DEMO-003', lead: 'Aarav Singh', title: 'Share AI & Machine Learning overview', due: '2026-10-18T10:00', priority: 'Medium', status: 'Pending' },
  { id: 'FU-DEMO-004', lead: 'Sneha Kulkarni', title: 'Discuss UI/UX portfolio expectations', due: '2026-10-19T11:00', priority: 'Low', status: 'Pending' },
  { id: 'FU-DEMO-005', lead: 'Kabir Deshmukh', title: 'Confirm web development demo agenda', due: '2026-10-17T12:00', priority: 'High', status: 'Completed' },
  { id: 'FU-DEMO-006', lead: 'Meera Joshi', title: 'Introduce Cloud & DevOps track', due: '2026-10-20T15:00', priority: 'Low', status: 'Pending' },
];

const leads = ['Rohan Sharma', 'Priya Patel', 'Aarav Singh', 'Sneha Kulkarni', 'Kabir Deshmukh', 'Meera Joshi'];
const dateLabel = (value: string) => new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata' });

export default function DemoFollowupsFallback() {
  const [tasks, setTasks] = useState<Task[]>(seed);
  const [lead, setLead] = useState(leads[0]);
  const [title, setTitle] = useState('Call to discuss course options');
  const [due, setDue] = useState('2026-10-18T11:00');
  const [priority, setPriority] = useState<Task['priority']>('Medium');
  const [ready, setReady] = useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length) setTasks(parsed);
      }
    } catch { /* Sample data remains available without browser storage. */ }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try { window.localStorage.setItem(KEY, JSON.stringify(tasks)); } catch { /* In-memory demo remains usable. */ }
  }, [ready, tasks]);

  function addTask(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !due) return;
    setTasks(previous => [{
      id: 'FU-DEMO-' + Date.now(),
      lead,
      title: title.trim(),
      due,
      priority,
      status: 'Pending',
    }, ...previous]);
    setTitle('');
    setNotice('Demo follow-up added in this browser only. No message or reminder was sent.');
  }

  const pending = tasks.filter(task => task.status === 'Pending').length;
  const completed = tasks.length - pending;

  return <div className="space-y-5">
    <div className="flex items-start gap-3 rounded-xl border border-[var(--color-warning)] bg-[var(--color-warning-soft)] px-4 py-3 text-xs leading-5 text-[var(--color-warning)]">
      <Sparkles size={15} className="mt-0.5 shrink-0" />
      <span><strong>Demo data only.</strong> These sample records are saved in this browser. They are not written to Supabase and do not send real messages or reminders.</span>
    </div>
    <div className="grid gap-4 sm:grid-cols-3">
      {[['Total follow-ups', tasks.length], ['Pending', pending], ['Completed', completed]].map(([label, value]) =>
        <div key={String(label)} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <p className="text-xs text-[var(--color-muted)]">{label}</p>
          <p className="mt-2 text-2xl font-bold">{value}</p>
          <p className="mt-1 text-[11px] text-[var(--color-subtle)]">Illustrative sample records</p>
        </div>)}
    </div>
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Follow-up queue</h2></div>
        <div className="space-y-3 p-5">
          {[...tasks].sort((a, b) => a.due.localeCompare(b.due)).map(task =>
            <div key={task.id} className="flex flex-col gap-3 rounded-xl border border-[var(--color-border)] p-4 sm:flex-row sm:items-center">
              <button type="button" onClick={() => setTasks(previous => previous.map(item => item.id === task.id ? { ...item, status: item.status === 'Completed' ? 'Pending' : 'Completed' } : item))} aria-label={task.status === 'Completed' ? 'Reopen task' : 'Complete task'} className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${task.status === 'Completed' ? 'border-emerald-500 bg-emerald-500/10 text-emerald-500' : 'border-[var(--color-border)] text-[var(--color-muted)]'}`}>
                <CheckCircle2 size={16} />
              </button>
              <div className="min-w-0 flex-1">
                <p className={`text-xs font-bold ${task.status === 'Completed' ? 'line-through text-[var(--color-subtle)]' : ''}`}>{task.title}</p>
                <p className="mt-1 text-xs text-[var(--color-muted)]">{task.lead}</p>
                <p className="mt-1 flex items-center gap-1 text-[10px] text-[var(--color-subtle)]"><Clock3 size={12} />{dateLabel(task.due)}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-raised)] px-2.5 py-1 text-[10px] font-semibold">{task.priority} priority</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-raised)] px-2.5 py-1 text-[10px] font-semibold">{task.status}</span>
              </div>
            </div>)}
        </div>
      </section>
      <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Create a demo follow-up</h2></div>
        <form onSubmit={addTask} className="space-y-4 p-5">
          <label className="block text-xs font-semibold">Lead
            <select value={lead} onChange={event => setLead(event.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs">{leads.map(item => <option key={item}>{item}</option>)}</select>
          </label>
          <label className="block text-xs font-semibold">Task title
            <input required value={title} onChange={event => setTitle(event.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs" />
          </label>
          <label className="block text-xs font-semibold">Due date and time
            <input required type="datetime-local" value={due} onChange={event => setDue(event.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs" />
          </label>
          <label className="block text-xs font-semibold">Priority
            <select value={priority} onChange={event => setPriority(event.target.value as Task['priority'])} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"><option>High</option><option>Medium</option><option>Low</option></select>
          </label>
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white"><Plus size={14} /> Save demo follow-up</button>
        </form>
        {notice && <p role="status" className="px-5 pb-5 text-xs text-[var(--color-success)]">{notice}</p>}
      </section>
    </div>
  </div>;
}
