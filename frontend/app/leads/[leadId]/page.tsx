'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  ArrowLeft, AlertTriangle, CalendarClock, CheckCircle2, Clock3, MessageSquare,
  ShieldCheck, UserRound, UserRoundCheck, UserRoundCog, ClipboardList, Send,
  PauseCircle, PlayCircle, Plus, X
} from 'lucide-react';
import { DEMO_MODE } from '@/lib/mode';
import { getDemoLeadDetail } from '@/fixtures/lead-details';
import { addLeadNote, createFollowUp, getLeadDetail, handoffLead, releaseLeadToAI, updateLeadStage } from '@/services/leads';
import type { LeadDetail, LeadStage, LeadTimelineEvent } from '@/types/api';

const stageOptions: { value: LeadStage; label: string }[] = [
  { value: 'new', label: 'New' }, { value: 'contacted', label: 'Contacted' },
  { value: 'qualified', label: 'Qualified' }, { value: 'demo_booked', label: 'Demo booked' },
  { value: 'demo_attended', label: 'Demo attended' }, { value: 'nurturing', label: 'Nurturing' },
  { value: 'admitted', label: 'Admitted' }, { value: 'lost', label: 'Lost' },
  { value: 'do_not_contact', label: 'Do not contact' },
];
const stageLabels: Record<string, string> = Object.fromEntries(stageOptions.map(s => [s.value, s.label]));
const formatDate = (value: string) => new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata' });
const sourceLabel = (value: string) => value.replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());

export default function LeadDetailPage() {
  const params = useParams<{ leadId: string }>();
  const leadId = decodeURIComponent(params.leadId);
  const original = useMemo(() => getDemoLeadDetail(leadId), [leadId]);
  const [lead, setLead] = useState<LeadDetail | null>(DEMO_MODE ? (original ?? null) : null);
  const [loading, setLoading] = useState(!DEMO_MODE);
  const [note, setNote] = useState('');
  const [followUpOpen, setFollowUpOpen] = useState(false);
  const [followUpText, setFollowUpText] = useState('Confirm approved course details with the admissions team.');
  const [followUpWhen, setFollowUpWhen] = useState('tomorrow');
  const [notice, setNotice] = useState('');
  const [events, setEvents] = useState<LeadTimelineEvent[]>(original?.timeline ?? []);

  useEffect(() => {
    if (DEMO_MODE) {
      setLead(original ?? null);
      setEvents(original?.timeline ?? []);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getLeadDetail(leadId)
      .then(result => {
        if (cancelled) return;
        setLead(result);
        setEvents(result.timeline ?? []);
      })
      .catch(error => {
        if (cancelled) return;
        setLead(null);
        setNotice(error instanceof Error ? error.message : 'Could not load this lead from the backend.');
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [leadId, original]);

  if (loading) {
    return <section className="mx-auto max-w-2xl rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center"><p className="text-sm text-[var(--color-muted)]">Loading lead from the FastAPI backend…</p></section>;
  }

  if (!lead) {
    return <section className="mx-auto max-w-2xl rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
      <AlertTriangle className="mx-auto text-[var(--color-warning)]" size={28} />
      <h1 className="mt-4 text-xl font-bold">Lead not found</h1>
      <p className="mt-2 text-sm text-[var(--color-muted)]">{notice || (DEMO_MODE ? 'This ID is not in the local demo fixtures.' : 'This lead was not returned by the backend lead-list endpoint.')}</p>
      <Link href="/leads" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--color-accent)]"><ArrowLeft size={16}/> Back to leads</Link>
    </section>;
  }

  const updateStage = async (stage: LeadStage) => {
    if (!DEMO_MODE) {
      try {
        await updateLeadStage(lead.id, stage);
      } catch (error) {
        setNotice(error instanceof Error ? error.message : 'Stage update failed.');
        return;
      }
    }
    setLead(current => current ? { ...current, stage } : current);
    setNotice(DEMO_MODE ? 'Stage changed in local demo state only; it was not persisted to the backend.' : 'Lead stage updated through the API.');
    setEvents(current => [{ id: `local-stage-${Date.now()}`, type: 'stage_change', title: DEMO_MODE ? 'Stage updated (demo)' : 'Stage updated', description: `Stage set to ${stageLabels[stage]}.`, occurred_at: new Date().toISOString(), actor: 'Current counselor' }, ...current]);
  };

  const toggleHandoff = async () => {
    const next = !lead.human_takeover;
    if (!DEMO_MODE) {
      try {
        if (next) await handoffLead(lead.id, 'human_requested');
        else if (lead.conversation_id) await releaseLeadToAI(lead.conversation_id);
        else {
          setNotice('Cannot release to AI: the API response did not include a conversation ID.');
          return;
        }
      } catch (error) {
        setNotice(error instanceof Error ? error.message : 'Handoff update failed.');
        return;
      }
    }
    setLead(current => current ? { ...current, human_takeover: next } : current);
    setNotice(DEMO_MODE
      ? (next ? 'Human takeover enabled locally. No live AI messages are affected.' : 'AI release recorded locally only; no real conversation was resumed.')
      : (next ? 'Human handoff requested through the API.' : 'Release-to-AI request completed through the API.'));
    setEvents(current => [{ id: `local-handoff-${Date.now()}`, type: 'handoff', title: next ? (DEMO_MODE ? 'Human takeover enabled (demo)' : 'Human takeover enabled') : (DEMO_MODE ? 'AI release selected (demo)' : 'Released to AI'), description: next ? 'AI replies should remain paused while a counselor owns the conversation.' : 'Release was explicitly requested by the counselor.', occurred_at: new Date().toISOString(), actor: 'Current counselor' }, ...current]);
  };

  const addNote = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const text = note.trim();
    if (!text) return;
    if (!DEMO_MODE) {
      try {
        await addLeadNote(lead.id, text);
      } catch (error) {
        setNotice(error instanceof Error ? error.message : 'Could not save note.');
        return;
      }
    }
    setEvents(current => [{ id: `local-note-${Date.now()}`, type: 'note', title: DEMO_MODE ? 'Counselor note (demo)' : 'Counselor note', description: text, occurred_at: new Date().toISOString(), actor: 'Current counselor' }, ...current]);
    setNote('');
    setNotice(DEMO_MODE ? 'Note added to local page state only. It is not stored on the server.' : 'Counselor note saved through the API.');
  };

  const addFollowUp = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const text = followUpText.trim();
    if (!text) return;
    if (!DEMO_MODE) {
      try {
        const due = new Date();
        if (followUpWhen === 'tomorrow') due.setDate(due.getDate() + 1);
        else if (followUpWhen === 'within 3 days') due.setDate(due.getDate() + 3);
        await createFollowUp({
          lead_id: lead.id,
          channel: Object.entries(lead.consent).find(([channel, allowed]) => allowed && channel !== 'marketing')?.[0] ?? 'internal',
          action_type: 'counselor_follow_up',
          reason: 'Created from the lead detail page',
          suggested_message: text,
          scheduled_at: due.toISOString(),
          priority: 'normal',
        });
      } catch (error) {
        setNotice(error instanceof Error ? error.message : 'Could not create follow-up.');
        return;
      }
    }
    setEvents(current => [{ id: `local-task-${Date.now()}`, type: 'follow_up', title: DEMO_MODE ? 'Follow-up task drafted (demo)' : 'Follow-up task created', description: `${text} · Due: ${followUpWhen}`, occurred_at: new Date().toISOString(), actor: 'Current counselor' }, ...current]);
    setFollowUpOpen(false);
    setNotice(DEMO_MODE ? 'Follow-up drafted locally. No message is scheduled or sent.' : 'Follow-up task created through the API. The worker must still enforce consent, opt-outs and quiet hours.');
  };

  const eventIcon = (type: string) => {
    if (type === 'message') return MessageSquare;
    if (type === 'follow_up') return CalendarClock;
    if (type === 'handoff') return UserRoundCog;
    if (type === 'note') return ClipboardList;
    if (type === 'booking') return CheckCircle2;
    return Clock3;
  };

  return <div className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <Link href="/leads" className="inline-flex items-center gap-2 text-xs font-semibold text-[var(--color-muted)] hover:text-[var(--color-accent)]"><ArrowLeft size={14}/> All leads</Link>
        <div className="mt-4 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-accent-soft)] text-sm font-bold text-[var(--color-accent)]">{lead.full_name.split(' ').map(part => part[0]).join('')}</div>
          <div><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-accent)]">Lead profile · {lead.id}</p><h1 className="mt-1 text-2xl font-bold tracking-tight">{lead.full_name}</h1><p className="mt-1 text-xs text-[var(--color-muted)]">{lead.course_interest ?? 'Course interest not recorded'} · {sourceLabel(lead.source)}</p></div>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button onClick={() => setFollowUpOpen(true)} className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs font-semibold hover:bg-[var(--color-raised)]"><Plus size={14}/> Create follow-up</button>
        <button onClick={toggleHandoff} className={`inline-flex items-center gap-2 rounded-lg px-3 py-2.5 text-xs font-semibold ${lead.human_takeover ? 'bg-[var(--color-warning-soft)] text-[var(--color-warning)]' : 'bg-[var(--color-accent-strong)] text-white hover:bg-[var(--color-accent)]'}`}>{lead.human_takeover ? <PlayCircle size={14}/> : <PauseCircle size={14}/>} {lead.human_takeover ? (DEMO_MODE ? 'Release to AI (demo)' : 'Release to AI') : 'Take over conversation'}</button>
      </div>
    </div>

    <div className="rounded-xl border border-[var(--color-warning)] bg-[var(--color-warning-soft)] px-4 py-3 text-xs leading-5 text-[var(--color-warning)]"><ShieldCheck className="mr-2 inline" size={15}/>{DEMO_MODE ? <><strong>Demo mode.</strong> All values are fictional. Changes stay in local page state; no messages, bookings, notes or tasks are sent or persisted.</> : <><strong>Limited live mode.</strong> The profile is derived from GET /api/leads. The current backend does not expose timeline, note, follow-up, stage-update or handoff routes, so those operations will report as unavailable rather than pretending to save.</>}</div>

    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(300px,0.8fr)]">
      <div className="space-y-5">
        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Lead overview</h2><span className="rounded-full bg-[var(--color-accent-soft)] px-3 py-1 text-[11px] font-semibold text-[var(--color-accent)]">Score {lead.lead_score}/100 · heuristic, not admission probability</span></div>
          <div className="grid gap-4 p-5 sm:grid-cols-2">
            <div><p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-subtle)]">Pipeline stage</p><select value={lead.stage} onChange={event => updateStage(event.target.value as LeadStage)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs font-semibold">{stageOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
            <div><p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-subtle)]">Assigned counselor</p><div className="mt-2 flex items-center gap-2 rounded-lg bg-[var(--color-raised)] px-3 py-2.5 text-xs"><UserRound size={15} className="text-[var(--color-subtle)]"/>{lead.assigned_name ?? 'Unassigned'}</div></div>
            <div><p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-subtle)]">Preferred language</p><p className="mt-2 rounded-lg bg-[var(--color-raised)] px-3 py-2.5 text-xs">{lead.preferred_language ?? 'Not recorded'}</p></div>
            <div><p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-subtle)]">Consent snapshot</p><div className="mt-2 flex flex-wrap gap-2">{Object.entries(lead.consent).map(([channel, enabled]) => <span key={channel} className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${enabled ? 'bg-[var(--color-success-soft)] text-[var(--color-success)]' : 'bg-[var(--color-raised)] text-[var(--color-muted)]'}`}>{channel.replaceAll('_', ' ')}: {enabled ? 'allowed in demo' : 'not allowed'}</span>)}</div></div>
          </div>
        </section>

        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Counselor summary</h2><p className="mt-1 text-[11px] text-[var(--color-muted)]">Evidence-based notes for handoff; verify current facts before replying.</p></div>
          <ul className="space-y-3 p-5">{lead.summary.map((line, index) => <li key={line} className="flex gap-3 text-xs leading-5 text-[var(--color-muted)]"><span className="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-accent-soft)] text-[10px] font-bold text-[var(--color-accent)]">{index + 1}</span>{line}</li>)}</ul>
        </section>

        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Conversation timeline</h2><p className="mt-1 text-[11px] text-[var(--color-muted)]">Messages, stage changes, notes and follow-up suggestions.</p></div>
          <div className="space-y-0 p-5">{events.map((item, index) => { const Icon = eventIcon(item.type); return <div key={item.id} className="relative flex gap-3 pb-5 last:pb-0"><div className="relative flex flex-col items-center"><div className="z-10 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-raised)] text-[var(--color-muted)]"><Icon size={14}/></div>{index < events.length - 1 && <div className="absolute top-8 h-full w-px bg-slate-200"/>}</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-start justify-between gap-2"><p className="text-xs font-semibold">{item.title}</p><time className="text-[10px] text-[var(--color-subtle)]">{formatDate(item.occurred_at)}</time></div><p className="mt-1 text-xs leading-5 text-[var(--color-muted)]">{item.description}</p><p className="mt-1 text-[10px] text-[var(--color-subtle)]">{item.actor ?? 'System'}{item.channel ? ` · ${sourceLabel(item.channel)}` : ''}</p></div></div>; })}</div>
        </section>
      </div>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Objections to address</h2></div>
          <div className="space-y-3 p-5">{lead.objections.length ? lead.objections.map(objection => <div key={objection.type} className="rounded-xl border border-[var(--color-border)] p-3"><div className="flex items-center gap-2"><AlertTriangle size={14} className="text-[var(--color-warning)]"/><p className="text-xs font-semibold">{objection.label}</p></div><p className="mt-2 text-[11px] leading-5 text-[var(--color-muted)]">{objection.evidence ?? 'No supporting evidence attached.'}</p></div>) : <p className="text-xs text-[var(--color-muted)]">No objections recorded. Ask discovery questions instead of assuming concerns.</p>}</div>
        </section>

        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Next best action</h2></div>
          <div className="p-5"><div className="flex gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--color-accent-soft)] text-[var(--color-accent)]"><CalendarClock size={17}/></div><p className="text-xs leading-5 text-[var(--color-muted)]">{lead.next_action}</p></div><button onClick={() => setFollowUpOpen(true)} className="mt-4 w-full rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white hover:bg-[var(--color-accent)]">Turn into follow-up task</button></div>
        </section>

        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Counselor note</h2></div>
          <form onSubmit={addNote} className="p-5"><label className="block text-xs font-medium text-[var(--color-muted)]" htmlFor="lead-note">Internal note<textarea id="lead-note" value={note} onChange={event => setNote(event.target.value)} rows={4} maxLength={1000} placeholder="Record a verified detail or next step..." className="mt-2 w-full resize-y rounded-lg border border-[var(--color-border)] px-3 py-2.5 text-xs outline-none focus:border-indigo-400"/></label><button type="submit" disabled={!note.trim()} className="mt-3 inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50"><ClipboardList size={14}/> Add note locally</button></form>
        </section>

        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
          <div className="border-b border-[var(--color-border)] px-5 py-4"><h2 className="text-sm font-bold">Contact & safety</h2></div>
          <div className="space-y-3 p-5"><div><p className="text-[10px] uppercase tracking-wider text-[var(--color-subtle)]">Phone</p><p className="mt-1 text-xs">{lead.phone ?? 'Not provided'}</p></div><div><p className="text-[10px] uppercase tracking-wider text-[var(--color-subtle)]">Email</p><p className="mt-1 break-all text-xs">{lead.email ?? 'Not provided'}</p></div><div className="rounded-lg bg-[var(--color-raised)] p-3 text-[11px] leading-5 text-[var(--color-muted)]"><ShieldCheck size={14} className="mr-1 inline"/>Consent and opt-out enforcement must be checked server-side before any outbound action.</div></div>
        </section>
      </aside>
    </div>

    {followUpOpen && <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--color-page)]/40 p-4"><form onSubmit={addFollowUp} className="w-full max-w-lg rounded-2xl bg-[var(--color-surface)] p-6 shadow-xl"><div className="flex items-center justify-between"><h2 className="text-lg font-bold">Draft follow-up</h2><button type="button" onClick={() => setFollowUpOpen(false)} aria-label="Close follow-up dialog"><X size={18}/></button></div><p className="mt-1 text-xs text-[var(--color-muted)]">Local demo task only; scheduling and delivery are not connected.</p><label className="mt-5 block text-xs font-semibold">Task description<textarea required value={followUpText} onChange={event => setFollowUpText(event.target.value)} rows={3} maxLength={500} className="mt-2 w-full rounded-lg border border-[var(--color-border)] px-3 py-2.5 text-xs"/></label><label className="mt-4 block text-xs font-semibold">Due window<select value={followUpWhen} onChange={event => setFollowUpWhen(event.target.value)} className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-xs"><option value="today">Today</option><option value="tomorrow">Tomorrow</option><option value="within 3 days">Within 3 days</option></select></label><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={() => setFollowUpOpen(false)} className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-xs">Cancel</button><button type="submit" className="rounded-lg bg-[var(--color-accent-strong)] px-4 py-2 text-xs font-semibold text-white"><Send size={13} className="mr-2 inline"/>Save draft</button></div></form></div>}
    {notice && <div role="status" className="fixed bottom-5 right-5 z-[60] flex max-w-sm items-start gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-xs shadow-xl"><CheckCircle2 size={16} className="shrink-0 text-[var(--color-success)]"/><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss notice"><X size={14}/></button></div>}
    <p className="text-center text-[10px] text-[var(--color-subtle)]">{DEMO_MODE ? 'Demo fixture' : 'Live API'} · Verify all records and authorization before production use.</p>
  </div>;
}
