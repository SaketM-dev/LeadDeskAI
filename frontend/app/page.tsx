'use client';

import Link from 'next/link';
import {
  ArrowRight, ArrowUpRight, AudioWaveform, Bot, BrainCircuit,
  CalendarCheck, Check, ChevronDown, CircleCheck, GraduationCap, Layers3,
  MessageSquareText, MousePointer2, ShieldCheck, Sparkles, Workflow, Zap
} from 'lucide-react';

const features = [
  { icon: MessageSquareText, number: '01', title: 'Every conversation, in one place', text: 'Bring student conversations into one focused inbox. Keep context close and make every reply feel personal.', color: 'text-violet-300', glow: 'bg-violet-400/10' },
  { icon: BrainCircuit, number: '02', title: 'Counselling that understands context', text: 'Give counsellors AI-assisted reply suggestions grounded in your approved course and admissions knowledge.', color: 'text-sky-300', glow: 'bg-sky-400/10' },
  { icon: Workflow, number: '03', title: 'Follow-ups that do not fall through', text: 'Organise next steps, prioritise high-intent leads and keep the admissions journey moving.', color: 'text-emerald-300', glow: 'bg-emerald-400/10' },
  { icon: GraduationCap, number: '04', title: 'Better-fit course recommendations', text: 'Connect student interests and aptitude signals to relevant learning paths and course conversations.', color: 'text-amber-200', glow: 'bg-amber-300/10' },
];

const workflow = [
  { step: '01', title: 'Capture', text: 'Bring enquiries into a shared lead pipeline.' },
  { step: '02', title: 'Understand', text: 'Keep student context, intent and conversations together.' },
  { step: '03', title: 'Guide', text: 'Use AI suggestions and knowledge to support counsellors.' },
  { step: '04', title: 'Convert', text: 'Make the next action clear, from follow-up to demo.' },
];

export default function HomePage() {
  return <main className="relative isolate min-h-screen overflow-hidden bg-[#080a11] text-white selection:bg-violet-400/30">
    <div className="pointer-events-none fixed inset-0 -z-10 opacity-70"><div className="landing-grid absolute inset-0"/><div className="absolute inset-x-0 top-0 h-[700px] bg-[radial-gradient(ellipse_at_top,rgba(46,48,110,0.2),transparent_65%)]"/></div>
    <header className="relative z-20 mx-auto flex h-[76px] max-w-[1240px] items-center justify-between px-5 sm:px-8">
      <Link href="/" aria-label="AI Lead Desk home" className="flex items-center gap-2.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06]"><Sparkles size={16} className="text-violet-200"/></span>
        <span className="text-sm font-semibold tracking-tight">lead<span className="text-violet-300">desk</span><span className="ml-1.5 rounded border border-white/10 px-1 py-0.5 text-[9px] font-medium uppercase tracking-widest text-white/45">AI</span></span>
      </Link>
      <nav aria-label="Main navigation" className="flex items-center gap-4 text-[11px] text-white/65 sm:gap-7 sm:text-xs">
        <a href="#features" className="transition hover:text-white">Features</a>
        <a href="#workflow" className="hidden transition hover:text-white sm:inline" >How it works</a>
        <a href="#why-leaddesk" className="hidden transition hover:text-white md:inline">Why LeadDesk</a>
        <Link href="/login" className="transition hover:text-white">Sign in</Link>
        <Link href="/dashboard" className="font-medium text-white transition hover:text-violet-200">Open workspace <span aria-hidden="true">↗</span></Link>
      </nav>
    </header>

    <section className="relative isolate mx-auto flex min-h-[690px] max-w-[1240px] flex-col items-center px-5 pb-20 pt-14 text-center sm:px-8 sm:pt-20 lg:min-h-[770px]">
      <div className="landing-orb left-1/2 top-[-70px] -z-10 -translate-x-1/2"/>
      <div className="landing-orb-ring left-1/2 top-[20px] -z-10 -translate-x-1/2"/>
      <div className="absolute left-1/2 top-[80px] -z-10 h-[480px] w-[min(90vw,900px)] -translate-x-1/2 rounded-full bg-indigo-500/[0.035] blur-3xl"/>
      <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.045] px-3.5 py-1.5 text-[10px] text-white/70 shadow-[0_0_30px_rgba(111,92,255,0.08)] sm:text-xs">
        <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-300 opacity-40"/><span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-300"/></span>
        The intelligent workspace for admissions teams <ArrowRight size={12} className="text-white/40"/>
      </div>
      <h1 className="mt-8 max-w-4xl text-[clamp(2.8rem,7vw,5.7rem)] font-medium leading-[0.99] tracking-[-0.065em]">
        More meaningful<br/><span className="bg-gradient-to-r from-white via-violet-100 to-violet-300 bg-clip-text text-transparent">student conversations.</span>
      </h1>
      <p className="mt-6 max-w-xl text-sm leading-7 text-white/55 sm:text-base">Less busywork. Better follow-through. One AI-powered admissions workspace that helps your team turn every enquiry into a clearer next step.</p>
      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Link href="/dashboard" className="group inline-flex min-h-11 items-center gap-2 rounded-full bg-white px-5 py-3 text-xs font-semibold text-[#101018] transition hover:bg-violet-100">Explore the workspace <ArrowRight size={14} className="transition group-hover:translate-x-0.5"/></Link>
        <a href="#features" className="inline-flex min-h-11 items-center gap-2 px-4 py-3 text-xs font-medium text-white/65 transition hover:text-white">Discover the platform <ArrowRight size={14}/></a>
      </div>

      <div className="relative mt-16 w-full max-w-[850px] sm:mt-20">
        <div className="absolute -inset-8 -z-10 rounded-[40%] bg-violet-500/[0.08] blur-3xl"/>
        <div className="landing-float relative mx-auto max-w-[790px] rounded-2xl border border-white/[0.13] bg-[#0d101a]/90 p-2 text-left shadow-[0_30px_100px_rgba(0,0,0,0.55)] backdrop-blur-xl sm:rounded-[22px] sm:p-3">
          <div className="flex items-center justify-between border-b border-white/[0.08] px-3 pb-3 pt-1 sm:px-4">
            <div className="flex items-center gap-2"><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-400/10 text-violet-200"><Layers3 size={14}/></span><span className="text-[11px] font-semibold">Admissions overview</span></div>
            <div className="flex items-center gap-1.5 text-[9px] text-white/40"><span className="h-1.5 w-1.5 rounded-full bg-emerald-300"/>{' '}Workspace preview</div>
          </div>
          <div className="grid gap-2 p-1.5 sm:grid-cols-[1.2fr_0.8fr] sm:gap-3 sm:p-3">
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.025] p-4 sm:p-5">
              <div className="flex items-start justify-between"><div><p className="text-[10px] text-white/45">Pipeline snapshot</p><p className="mt-2 text-2xl font-medium tracking-tight">Student journey <span className="text-violet-200">↗</span></p></div><span className="rounded-lg border border-white/10 p-2 text-violet-200"><Workflow size={15}/></span></div>
              <div className="mt-5 grid grid-cols-3 gap-2">
                {[['New leads','32','bg-sky-300'],['In progress','18','bg-violet-300'],['Qualified','12','bg-emerald-300']].map(([label,value,color])=><div key={label} className="rounded-lg border border-white/[0.07] bg-black/20 p-2.5 sm:p-3"><span className={`mb-2 block h-1 w-5 rounded-full ${color}`}/><p className="text-[9px] text-white/45 sm:text-[10px]">{label}</p><p className="mt-1 text-lg font-medium">{value}</p></div>)}
              </div>
              <div className="mt-4 rounded-lg border border-white/[0.07] bg-black/15 p-3"><div className="flex items-center justify-between text-[10px]"><span className="text-white/50">Pipeline momentum</span><span className="text-emerald-200">Next step ready</span></div><div className="mt-2 flex h-1.5 gap-1 overflow-hidden rounded-full"><span className="w-[32%] rounded-full bg-sky-300"/><span className="w-[25%] rounded-full bg-violet-300"/><span className="w-[18%] rounded-full bg-emerald-300"/><span className="flex-1 rounded-full bg-white/10"/></div></div>
            </div>
            <div className="flex flex-col gap-2 sm:gap-3">
              <div className="flex-1 rounded-xl border border-violet-300/15 bg-gradient-to-br from-violet-400/[0.11] to-white/[0.02] p-4"><div className="flex items-center gap-2"><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-300/10 text-violet-200"><Bot size={15}/></span><span className="text-[10px] font-semibold">AI copilot</span><span className="ml-auto rounded-full bg-emerald-300/10 px-2 py-1 text-[8px] text-emerald-200">Suggestion</span></div><p className="mt-3 text-xs leading-5 text-white/75">“Based on your interest in data science, here are the course options I’d recommend exploring…”</p><div className="mt-3 flex items-center gap-2 text-[9px] text-white/35"><Sparkles size={11}/> Context-aware draft · Review before sending</div></div>
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.025] p-4"><div className="flex items-center justify-between"><span className="text-[10px] text-white/45">Next follow-up</span><CalendarCheck size={14} className="text-amber-200"/></div><p className="mt-2 text-xs font-medium">Course consultation</p><p className="mt-1 text-[10px] text-white/40">A clear next step for every lead.</p></div>
            </div>
          </div>
          <div className="flex items-center justify-between border-t border-white/[0.07] px-3 py-2.5 text-[9px] text-white/35 sm:px-4"><span className="flex items-center gap-2"><ShieldCheck size={12}/> Designed for counsellor-led workflows</span><span>Illustrative preview</span></div>
        </div>
        <div className="landing-float absolute -left-2 top-[22%] hidden items-center gap-2 rounded-xl border border-white/10 bg-[#111420]/90 px-3 py-2.5 text-left shadow-xl backdrop-blur-xl sm:flex" style={{animationDelay:'-2s'}}><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-300/10 text-emerald-200"><CircleCheck size={14}/></span><span><span className="block text-[10px] font-semibold">Lead qualified</span><span className="mt-0.5 block text-[9px] text-white/40">Next step identified</span></span></div>
        <div className="landing-float absolute -right-1 bottom-[15%] hidden items-center gap-2 rounded-xl border border-white/10 bg-[#111420]/90 px-3 py-2.5 text-left shadow-xl backdrop-blur-xl sm:flex" style={{animationDelay:'-4s'}}><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-sky-300/10 text-sky-200"><AudioWaveform size={14}/></span><span><span className="block text-[10px] font-semibold">Inbox, in sync</span><span className="mt-0.5 block text-[9px] text-white/40">Conversation context</span></span></div>
      </div>
      <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-[10px] text-white/35 sm:text-[11px]"><span className="flex items-center gap-2"><Check size={12} className="text-violet-300"/> One student timeline</span><span className="flex items-center gap-2"><Check size={12} className="text-violet-300"/> Human-reviewed AI</span><span className="flex items-center gap-2"><Check size={12} className="text-violet-300"/> Clear next actions</span></div>
    </section>

    <section id="features" className="relative mx-auto max-w-[1240px] scroll-mt-20 px-5 py-20 sm:px-8 sm:py-28">
      <div className="absolute left-1/2 top-0 -z-10 h-64 w-[80%] -translate-x-1/2 bg-violet-500/[0.045] blur-[100px]"/>
      <div className="mx-auto max-w-2xl text-center"><p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-violet-200/80">One connected workspace</p><h2 className="mt-4 text-3xl font-medium tracking-[-0.045em] sm:text-5xl">Everything that moves a student forward.</h2><p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-white/50">The essential tools for admissions teams, brought together in a calm, focused workflow.</p></div>
      <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:mt-16 lg:grid-cols-4">
        {features.map(feature=>{const Icon=feature.icon;return <article key={feature.number} className="group relative overflow-hidden rounded-2xl border border-white/[0.09] bg-white/[0.025] p-5 transition duration-300 hover:-translate-y-1 hover:border-violet-300/25 hover:bg-white/[0.04] sm:p-6"><div className={`flex h-10 w-10 items-center justify-center rounded-xl ${feature.glow} ${feature.color}`}><Icon size={18}/></div><div className="mt-8 flex items-center justify-between"><span className="text-[10px] font-medium tracking-widest text-white/30">FEATURE {feature.number}</span><ArrowUpRight size={14} className="text-white/25 transition group-hover:text-violet-200"/></div><h3 className="mt-3 text-base font-medium leading-6">{feature.title}</h3><p className="mt-3 text-xs leading-6 text-white/50">{feature.text}</p></article>})}
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <article className="rounded-2xl border border-white/[0.09] bg-gradient-to-br from-violet-400/[0.08] to-transparent p-6 sm:p-7"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-300/10 text-violet-200"><Zap size={17}/></span><h3 className="mt-5 text-lg font-medium">A smarter daily rhythm</h3><p className="mt-2 text-xs leading-6 text-white/50">See what needs attention, organise follow-ups and keep the team aligned on next actions.</p><Link href="/followups" className="mt-5 inline-flex items-center gap-2 text-xs text-violet-200 hover:text-white">Explore follow-ups <ArrowRight size={13}/></Link></article>
        <article className="rounded-2xl border border-white/[0.09] bg-white/[0.025] p-6 sm:p-7"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-300/10 text-sky-200"><MousePointer2 size={17}/></span><h3 className="mt-5 text-lg font-medium">A clear view of every lead</h3><p className="mt-2 text-xs leading-6 text-white/50">Move from pipeline overview to student context without losing the thread.</p><Link href="/leads" className="mt-5 inline-flex items-center gap-2 text-xs text-sky-200 hover:text-white">Explore leads <ArrowRight size={13}/></Link></article>
        <article className="rounded-2xl border border-white/[0.09] bg-white/[0.025] p-6 sm:p-7"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-300/10 text-emerald-200"><ShieldCheck size={17}/></span><h3 className="mt-5 text-lg font-medium">Knowledge with guardrails</h3><p className="mt-2 text-xs leading-6 text-white/50">Keep approved guidance close to counsellors and review AI-assisted replies before sending.</p><Link href="/knowledge" className="mt-5 inline-flex items-center gap-2 text-xs text-emerald-200 hover:text-white">Explore knowledge base <ArrowRight size={13}/></Link></article>
      </div>
    </section>

    <section id="workflow" className="scroll-mt-20 border-y border-white/[0.07] bg-white/[0.015]">
      <div className="mx-auto grid max-w-[1240px] gap-10 px-5 py-20 sm:px-8 sm:py-24 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
        <div><p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-violet-200/80">From enquiry to next step</p><h2 className="mt-4 text-3xl font-medium tracking-[-0.045em] sm:text-4xl">Less tab-hopping.<br/>More forward motion.</h2><p className="mt-4 max-w-md text-sm leading-7 text-white/50">A connected workflow helps your team understand the student, respond thoughtfully and know what should happen next.</p><Link href="/dashboard" className="mt-7 inline-flex items-center gap-2 text-xs font-medium text-white hover:text-violet-200">See the workspace <ArrowRight size={14}/></Link></div>
        <div className="divide-y divide-white/[0.08]">{workflow.map((item,index)=><div key={item.step} className="group grid grid-cols-[42px_1fr_20px] items-start gap-4 py-5 first:pt-0 last:pb-0 sm:grid-cols-[54px_1fr_20px]"><span className="pt-1 text-xs font-medium text-violet-200/65">{item.step}</span><div><h3 className="text-sm font-medium">{item.title}</h3><p className="mt-1.5 text-xs leading-6 text-white/45">{item.text}</p></div><ChevronDown size={15} className={`mt-1 text-white/25 transition group-hover:translate-y-0.5 ${index===workflow.length-1?'rotate-[-90deg]':''}`}/></div>)}</div>
      </div>
    </section>

    <section id="why-leaddesk" className="mx-auto max-w-[1240px] scroll-mt-20 px-5 py-20 sm:px-8 sm:py-24">
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-[#10121d] px-6 py-10 sm:px-12 sm:py-14">
        <div className="landing-orb right-[-180px] top-[-250px] opacity-50"/>
        <div className="relative grid items-center gap-8 lg:grid-cols-[1fr_auto]"><div><p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-violet-200/80">Built for people-first admissions</p><h2 className="mt-4 max-w-2xl text-3xl font-medium tracking-[-0.045em] sm:text-4xl">AI helps with the busywork.<br/><span className="text-white/50">People lead the conversation.</span></h2><p className="mt-4 max-w-xl text-sm leading-7 text-white/50">LeadDesk brings structure to your process while keeping counsellors in control of student-facing decisions.</p></div><Link href="/dashboard" className="inline-flex min-h-11 items-center justify-center gap-2 self-center rounded-full bg-white px-5 py-3 text-xs font-semibold text-[#101018] transition hover:bg-violet-100">Open LeadDesk <ArrowRight size={14}/></Link></div>
      </div>
    </section>

    <footer className="border-t border-white/[0.08]">
      <div className="mx-auto flex max-w-[1240px] flex-col gap-5 px-5 py-8 text-[10px] text-white/40 sm:flex-row sm:items-center sm:justify-between sm:px-8"><Link href="/" className="flex items-center gap-2 font-semibold text-white/70"><Sparkles size={14} className="text-violet-200"/> lead<span className="-ml-2 text-violet-300">desk</span><span className="font-normal text-white/35">AI</span></Link><div className="flex flex-wrap gap-x-5 gap-y-3"><a href="#features" className="hover:text-white">Features</a><a href="#workflow" className="hover:text-white">How it works</a><Link href="/login" className="hover:text-white">Sign in</Link><Link href="/dashboard" className="hover:text-white">Workspace</Link></div><span>© {new Date().getFullYear()} AI Lead Desk</span></div>
    </footer>
  </main>;
}
