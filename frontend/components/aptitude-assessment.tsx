'use client';

import { useEffect, useState } from 'react';
import { Check, CheckCircle2, ChevronLeft, ChevronRight, ClipboardCheck, LoaderCircle, RotateCcw, Sparkles } from 'lucide-react';
import { DEMO_MODE } from '@/lib/mode';

type Option = { key: string; label: string | Record<string, string> };
type Question = { id: string; question: string | Record<string, string>; options: Option[]; answered_count?: number };
type Lead = { id: string; full_name: string };
type Result = { score: number; result_summary: string; recommended_course_ids: string[]; recommendation_rationale: string; dimension_scores?: {dimension:string;points:number}[] };
type Assessment = { id: string; status: string; language: string; goal_summary?: string; score?: number; result_summary?: string; recommended_course_ids?: string[]; recommendation_rationale?: string };

const DEMO_LEADS: Lead[] = [
  { id: 'demo-rohan', full_name: 'Rohan Sharma' },
  { id: 'demo-priya', full_name: 'Priya Patel' },
  { id: 'demo-aarav', full_name: 'Aarav Singh' },
];
const CAREER_QUESTIONS: string[][] = [
  ["Which hands-on project sounds most satisfying?", "Repair a machine or assemble equipment", "Investigate why a system behaves unexpectedly", "Create an original visual or story", "Help a person learn a new skill", "Pitch a project and lead the team", "Organize records and check every detail"],
  ["Which school or work task would you choose?", "Build or maintain something tangible", "Analyze evidence to answer a difficult question", "Design a presentation with a distinctive style", "Support someone who is struggling", "Coordinate a group toward a goal", "Create a clear checklist and keep it accurate"],
  ["A community center needs help. What would you do?", "Set up equipment and the physical space", "Study survey results to identify needs", "Create posters and engaging materials", "Welcome visitors and guide participants", "Recruit volunteers and promote the event", "Track registrations, schedules, and supplies"],
  ["Which challenge would you most enjoy solving?", "Find and fix a mechanical fault", "Test possible explanations using data", "Develop a fresh concept or design", "Resolve a misunderstanding between people", "Negotiate resources for a promising idea", "Find the source of an error in a detailed record"],
  ["Choose a weekend project.", "Build a shelf or practical device", "Explore a science question and record findings", "Make a short film, illustration, or song", "Volunteer to tutor someone", "Organize a small market or fundraiser", "Plan a budget and maintain an inventory"],
  ["Which result would make you proudest?", "A device that works reliably", "A conclusion supported by strong evidence", "A creative work that expresses an idea", "A person who feels supported and capable", "A team that reaches an ambitious target", "A process that is accurate and orderly"],
  ["In a new workplace, which task attracts you?", "Operate tools or technical equipment", "Research a complex topic", "Create content or visual concepts", "Train or advise colleagues", "Present proposals to decision-makers", "Maintain schedules and documentation"],
  ["How would you improve a local service?", "Inspect and improve its physical setup", "Measure performance and investigate patterns", "Redesign its communication and appearance", "Interview users and support their needs", "Build partnerships to expand its reach", "Standardize procedures and track service quality"],
  ["Which activity would you prefer during a project?", "Install, test, or repair components", "Compare evidence and evaluate hypotheses", "Brainstorm and prototype original ideas", "Facilitate discussion and help teammates", "Set priorities and persuade stakeholders", "Maintain the project plan and quality checks"],
  ["A team has a difficult deadline. What role fits you?", "Handle practical setup and technical tasks", "Identify the root cause of delays", "Find an inventive alternative approach", "Keep the team supported and communicating", "Make decisions and rally the team", "Track milestones and catch omissions"],
  ["Which course assignment sounds appealing?", "Build a working model", "Conduct a structured investigation", "Create a portfolio piece", "Design a lesson or support plan", "Prepare a business pitch", "Audit a dataset for accuracy"],
  ["Which tool would you most like to use?", "Workshop tools or diagnostic equipment", "A lab, analytical software, or research database", "Illustration, editing, or design software", "Learning materials or coaching resources", "Presentation, sales, or planning tools", "Spreadsheets, filing systems, or checklists"],
  ["When faced with a new topic, you prefer to…", "Learn by doing and practicing techniques", "Ask questions and examine evidence", "Explore ideas and express them creatively", "Discuss it with others and share understanding", "Consider how to turn it into an opportunity", "Organize information into a dependable system"],
  ["Which responsibility sounds most rewarding?", "Keep equipment safe and operational", "Find insights that others have missed", "Shape the look and feel of an experience", "Help people develop their abilities", "Lead an initiative from idea to result", "Ensure records and processes are correct"],
  ["What would you most enjoy improving?", "The performance of a physical product", "The quality of a prediction or explanation", "The originality of a campaign or design", "The experience of people using a service", "The reach or impact of an organization", "The consistency of an operational process"],
  ["Pick a problem to work on.", "A piece of equipment keeps failing", "Conflicting evidence needs to be understood", "A message is dull and hard to notice", "People cannot access the help they need", "A useful idea needs support and funding", "Important information is disorganized"],
  ["Which internship task would you choose?", "Assist with fieldwork or technical maintenance", "Summarize research and analyze results", "Create content for a campaign", "Help customers or program participants", "Support sales, outreach, or partnerships", "Update reports and verify information"],
  ["How do you prefer to contribute to a group?", "Turn plans into practical results", "Bring careful reasoning and evidence", "Offer imaginative approaches", "Listen, explain, and encourage", "Take initiative and build momentum", "Keep work organized and dependable"],
  ["Which achievement would interest you most?", "Making a process or product work better", "Discovering a reliable explanation", "Producing an original piece of work", "Helping a group overcome a challenge", "Growing a project or initiative", "Making a system more accurate"],
  ["A small organization asks for your help. You would…", "Set up or repair its equipment", "Study its data to find improvement areas", "Refresh its branding and materials", "Talk with the people it serves", "Develop a plan to attract partners", "Create a tracking and reporting system"],
  ["Which environment sounds comfortable?", "A workshop, site, studio, or active practical setting", "A research-focused environment with time to investigate", "A flexible space for creative exploration", "A collaborative setting centered on people", "A fast-moving setting with goals and decisions", "A structured setting with clear processes"],
  ["What kind of question captures your curiosity?", "How is this built and how can it be fixed?", "What explains this pattern and what evidence supports it?", "What new form could this idea take?", "What would help this person or group?", "How could this idea persuade or scale?", "How can we make this process consistent?"],
  ["Which task would you volunteer for?", "Set up an event's technical equipment", "Evaluate feedback and draw conclusions", "Create the event's visual identity", "Welcome and guide attendees", "Promote the event and find sponsors", "Manage attendance lists and schedules"],
  ["What do you do when a process is inefficient?", "Try a practical fix and test it", "Measure the issue and identify its cause", "Imagine a more original approach", "Ask affected people what they need", "Convince others to adopt an improvement", "Document the steps and remove errors"],
  ["Which kind of feedback helps you most?", "Whether the solution works in practice", "Whether the reasoning follows the evidence", "Whether the result is original and expressive", "Whether it helps people feel understood", "Whether it achieves its intended impact", "Whether it is correct and complete"],
  ["Choose a goal for a personal project.", "Make or repair something useful", "Answer a question through investigation", "Publish a creative piece", "Teach or support a community", "Launch an initiative or small venture", "Build an organized reference or tracker"],
  ["Which work would you like to learn?", "Operating, assembling, or maintaining equipment", "Research methods and analytical thinking", "Writing, visual design, or creative production", "Counseling, teaching, or community support", "Leadership, negotiation, or entrepreneurship", "Quality assurance, records, or process management"],
  ["A new idea is proposed. Your first instinct is to…", "Work out what it would take to build it", "Check the assumptions and evidence", "Explore different concepts and possibilities", "Consider who it would help and how", "Think about how to gain support for it", "Identify requirements, risks, and steps"],
  ["What would you most enjoy at a career fair?", "Demonstrations of tools and practical work", "Talks about research and discovery", "Exhibitions of creative work", "Stories about teaching and helping roles", "Meetings with founders and team leaders", "Learning about operations and quality systems"],
  ["At the end of a successful day, you would like to have…", "Built, fixed, or completed something practical", "Learned something through careful investigation", "Created something distinctive", "Helped someone make progress", "Moved a team or goal forward", "Made information and processes accurate"]
];
const CAREER_DIMENSIONS = ['realistic','investigative','artistic','social','enterprising','conventional'];
const DEMO_QUESTIONS = CAREER_QUESTIONS.map(([question, ...activities]) => ({
  question: { en: question },
  options: activities.map((activity, index) => ({ key: CAREER_DIMENSIONS[index], label: { en: activity } })),
}));

const COURSE_BY_DIMENSION: Record<string,string> = {
  realistic:'Applied Technology, Engineering and Technical Operations',
  investigative:'Data Science, Research and Analytical Problem Solving',
  artistic:'Design, Media and Creative Technology',
  social:'Teaching, Counseling and People-Centered Services',
  enterprising:'Business, Entrepreneurship and Product Leadership',
  conventional:'Operations, Quality Assurance and Information Management',
};
const panel='rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]';
const label=(value: string | Record<string,string> | undefined, language: string) =>
  typeof value === 'string' ? value : value?.[language] || value?.en || '';

export default function AptitudeAssessment() {
  const [leads,setLeads]=useState<Lead[]>(DEMO_MODE?DEMO_LEADS:[]);
  const [leadId,setLeadId]=useState('');
  const [language,setLanguage]=useState('en');
  const [goal,setGoal]=useState('');
  const [assessment,setAssessment]=useState<Assessment|null>(null);
  const [questions,setQuestions]=useState<Question[]>([]);
  const [index,setIndex]=useState(0);
  const [selected,setSelected]=useState<Record<string,string>>({});
  const [result,setResult]=useState<Result|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  const demoModeActive=DEMO_MODE;

  const current=questions[index];
  const progress=questions.length ? Math.round((Object.keys(selected).length/questions.length)*100) : 0;


  useEffect(()=>{
    if(DEMO_MODE) return;
    let cancelled=false;
    const token=sessionStorage.getItem('lead-desk-api-token');
    if(!token){setError('Save your LEAD_DESK_API_TOKEN in Workspace → Settings & access before starting a saved assessment.');return;}
    fetch('/backend-api/v1/leads?limit=100',{headers:{Authorization:'Bearer '+token}})
      .then(async r=>{const d=await r.json();if(!r.ok)throw new Error(d.detail||'Could not load leads');return d;})
      .then(d=>{if(!cancelled){setLeads((d.data||[]).map((l:Lead)=>({id:l.id,full_name:l.full_name})));setError('');}})
      .catch(e=>{if(!cancelled)setError(e instanceof Error?e.message:'Could not load leads.');});
    return ()=>{cancelled=true;};
  },[]);

  async function request(path:string,init:RequestInit={}) {
    const response=await fetch('/backend-api/v1/aptitude'+path,{...init,headers:{'Content-Type':'application/json',...(typeof window!=='undefined' && sessionStorage.getItem('lead-desk-api-token') ? {Authorization:'Bearer '+sessionStorage.getItem('lead-desk-api-token')} : {}),...init.headers}});
    const body=await response.json().catch(()=>({detail:'Unexpected server response'}));
    if(!response.ok) throw new Error(typeof body.detail==='string'?body.detail:'Assessment request failed.');
    return body;
  }

  function startDemo() {
    setAssessment({id:'demo-'+Date.now(),status:'in_progress',language});
    setQuestions(DEMO_QUESTIONS.map((q,i)=>({id:'demo-q-'+i,question:q.question,options:q.options})));
    setSelected({});setIndex(0);setResult(null);setError('');setNotice('Demo assessment started. Answers are stored only in this page session.');
  }

  async function start() {
    if(!leadId){setError('Select a lead before starting the assessment.');return;}
    setLoading(true);setError('');setNotice('');
    try {
      if(demoModeActive){startDemo();return;}
      const started=await request('/assessments',{method:'POST',body:JSON.stringify({lead_id:leadId,language,goal_summary:goal})});
      setAssessment(started.data);
      setQuestions([]);setSelected({});setIndex(0);setResult(null);
      await loadNext(String(started.data.id),{});
    } catch(e){setError(e instanceof Error?e.message:'Could not start assessment.');}
    finally{setLoading(false);}
  }

  async function loadNext(id:string, prior:Record<string,string>) {
    const response=await request('/assessments/'+encodeURIComponent(id)+'/next-question');
    if(response.data){
      setQuestions(previous=>[...previous,response.data]);
      setIndex(Object.keys(prior).length);
    } else if(response.all_answered) {
      const completed=await request('/assessments/'+encodeURIComponent(id)+'/complete',{method:'POST'});
      setResult(completed.data);
      setNotice(completed.notice||'Assessment completed and saved.');
    } else if(response.completed) {
      setResult(response.result||null);
    }
  }

  async function choose(key:string) {
    if(!current||!assessment||loading)return;
    setSelected(previous=>({...previous,[current.id]:key}));
    setError('');
    if(demoModeActive){return;}
    setLoading(true);
    try {
      await request('/assessments/'+encodeURIComponent(assessment.id)+'/responses',{method:'POST',body:JSON.stringify({question_id:current.id,selected_option_key:key})});
      await loadNext(assessment.id,{...selected,[current.id]:key});
    } catch(e){setError(e instanceof Error?e.message:'Could not save answer.');setSelected(previous=>{const copy={...previous};delete copy[current.id];return copy;});}
    finally{setLoading(false);}
  }

  async function finishDemo() {
    const points:Record<string,number>={};
    Object.values(selected).forEach(key=>{points[key]=(points[key]||0)+1;});
    const ranked=Object.entries(points).sort((a,b)=>b[1]-a[1]);
    const dimensions=ranked.map(([dimension,points])=>({dimension,points}));
    setResult({
      score:Math.round(Object.keys(selected).length/DEMO_QUESTIONS.length*100),
      result_summary:ranked.length?'Your selected answers lean toward '+ranked[0][0]+'. This reflects expressed interests, not ability.':'No result available.',
      recommended_course_ids:ranked.map(([key])=>COURSE_BY_DIMENSION[key]).filter(Boolean).slice(0,3),
      recommendation_rationale:'Interest counts: '+ranked.map(([k,v])=>k+'='+v).join(', ')+'. Discuss options with a counselor; this is not an admissions decision.',
      dimension_scores:dimensions,
    });
    setAssessment(previous=>previous?{...previous,status:'completed'}:previous);
  }

  async function finish() {
    if(!assessment)return;
    if(demoModeActive){finishDemo();return;}
    setLoading(true);setError('');
    try{const completed=await request('/assessments/'+encodeURIComponent(assessment.id)+'/complete',{method:'POST'});setResult(completed.data);setNotice(completed.notice||'Assessment saved.');setAssessment({...assessment,status:'completed'});}
    catch(e){setError(e instanceof Error?e.message:'Could not complete assessment.');}
    finally{setLoading(false);}
  }

  function reset(){setAssessment(null);setQuestions([]);setSelected({});setIndex(0);setResult(null);setError('');setNotice('');}
  const displayQuestion=current?label(current.question,language):'';
  const selectedCount=Object.keys(selected).length;

  return <div className="space-y-5">
    <div className={panel+' flex flex-col gap-4 p-5 md:flex-row md:items-end md:justify-between'}>
      <div className="max-w-2xl"><div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-accent)]"><ClipboardCheck size={16}/> INTEREST-LED ASSESSMENT <span className={'rounded-full px-2 py-1 text-[10px] '+(demoModeActive?'bg-[var(--color-warning-soft)] text-[var(--color-warning)]':'bg-[var(--color-success-soft)] text-[var(--color-success)]')}>{demoModeActive?'DEMO · LOCAL ONLY':'LIVE · PERSISTED'}</span></div><h2 className="mt-3 text-xl font-bold">Discover learning preferences</h2><p className="mt-2 text-xs leading-5 text-[var(--color-muted)]">A structured 30-item career-interest inventory explores six work-interest areas to guide a counselor conversation. Results are saved for live assessments and are intended only to support a counselor conversation.</p></div>
      <label className="text-xs font-semibold">Language<select value={language} onChange={e=>setLanguage(e.target.value)} className="mt-2 block w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2.5 md:w-40"><option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option><option value="mixed">Mixed</option></select></label>
    </div>

    {!assessment&&<div className={panel+' p-5'}>
      <h3 className="text-sm font-bold">Start an assessment</h3>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="text-xs font-semibold">Lead<select value={leadId} onChange={e=>setLeadId(e.target.value)} className="mt-2 block w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2.5"><option value="">Choose a lead</option>{leads.map(l=><option key={l.id} value={l.id}>{l.full_name}</option>)}</select></label>
        <label className="text-xs font-semibold">Learning goal (optional)<input value={goal} onChange={e=>setGoal(e.target.value)} maxLength={1000} placeholder="e.g. explore data or build websites" className="mt-2 block w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2.5"/></label>
      </div>
      {!DEMO_MODE&&leads.length===0&&<p className="mt-3 text-xs text-[var(--color-muted)]">Create a lead first. The live assessment is linked to a real lead record.</p>}
      <button disabled={!leadId||loading} onClick={start} className="mt-5 inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-40">{loading?<LoaderCircle size={14} className="animate-spin"/>:<Sparkles size={14}/>} Start assessment</button>
      {notice&&<p role="status" className="mt-3 text-xs text-[var(--color-muted)]">{notice}</p>}
    </div>}

    {assessment&&!result&&current&&<div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
      <section className={panel+' p-5'}>
        <div className="flex items-center justify-between gap-3"><span className="text-xs font-semibold text-[var(--color-muted)]">Question {index+1} of 30</span><span className="text-xs text-[var(--color-subtle)]">{Math.round((selectedCount/30)*100)}% answered</span></div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--color-raised)]"><div className="h-full rounded-full bg-[var(--color-accent-strong)] transition-all" style={{width:(selectedCount/30*100)+'%'}}/></div>
        <h3 className="mt-6 text-lg font-bold leading-7">{displayQuestion}</h3>
        <p className="mt-2 text-xs text-[var(--color-muted)]">{language==='hi'?'वह विकल्प चुनें जो आपकी रुचि को सबसे अच्छी तरह दर्शाता है।':language==='mr'?'तुमची आवड सर्वात चांगल्या प्रकारे दर्शवणारा पर्याय निवडा.':'Choose the option that best reflects the learner’s interests. There are no right or wrong answers.'}</p>
        <div className="mt-5 space-y-3">{current.options.map(o=><button key={o.key} disabled={loading||Boolean(selected[current.id])&&!demoModeActive} onClick={()=>choose(o.key)} className={'flex w-full items-center gap-3 rounded-xl border p-4 text-left text-xs transition '+(selected[current.id]===o.key?'border-[var(--color-accent)] bg-[var(--color-accent-soft)] text-[var(--color-accent)]':'border-[var(--color-border)] hover:border-[var(--color-accent)]')+' disabled:cursor-not-allowed disabled:opacity-70'}><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-current">{selected[current.id]===o.key&&<Check size={12}/>}</span>{label(o.label,language)}</button>)}</div>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3"><button disabled={index===0||loading} onClick={()=>setIndex(i=>i-1)} className="inline-flex items-center gap-1 rounded-lg border border-[var(--color-border)] px-4 py-2.5 text-xs disabled:opacity-40"><ChevronLeft size={14}/> Previous</button>{index<29?<button disabled={!selected[current.id]||loading} onClick={()=>{if(index<questions.length-1)setIndex(i=>i+1)}} className="inline-flex items-center gap-1 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-40">Next question <ChevronRight size={14}/></button>:<button disabled={selectedCount<30||loading} onClick={finish} className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-40">{loading?<LoaderCircle size={14} className="animate-spin"/>:<CheckCircle2 size={14}/>} Complete and save</button>}</div>
      </section>
      <aside className={panel+' p-5'}><div className="flex items-center gap-2 text-[var(--color-purple)]"><Sparkles size={18}/><h3 className="text-sm font-bold text-[var(--color-text)]">How results are used</h3></div><div className="mt-4 space-y-3 text-xs leading-5 text-[var(--color-muted)]">{['Answers indicate expressed interests, not innate ability or predicted success.','Recommendations include the strongest interest areas for counselor discussion.','A counselor should confirm course prerequisites, fees and current availability.'].map(t=><p key={t} className="flex gap-2"><CheckCircle2 size={15} className="mt-0.5 shrink-0 text-[var(--color-success)]"/>{t}</p>)}</div><p className="mt-5 rounded-xl border border-amber-300/20 bg-amber-300/[0.05] p-3 text-[11px] leading-5 text-[var(--color-muted)]">This is not a validated psychometric test and must not be used to decide admission eligibility.</p></aside>
    </div>}

    {assessment&&!current&&!result&&<div className={panel+' p-5'}><p className="text-sm">All questions have been answered.</p><button onClick={finish} disabled={loading} className="mt-4 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white">Complete and save</button></div>}

    {result&&<div className="grid gap-5 lg:grid-cols-[1.3fr_1fr]">
      <section className={panel+' p-5'}><div className="flex items-center gap-2 text-[var(--color-success)]"><CheckCircle2 size={19}/><h3 className="text-sm font-bold text-[var(--color-text)]">Assessment result {demoModeActive?'· demo result':'· saved result'}</h3></div><p className="mt-4 text-sm font-semibold">{result.result_summary}</p><div className="mt-4 grid gap-3 sm:grid-cols-2"><div className="rounded-xl bg-[var(--color-raised)] p-4"><p className="text-xs text-[var(--color-muted)]">Completion</p><p className="mt-1 text-2xl font-bold">{result.score}%</p><p className="mt-1 text-[10px] text-[var(--color-subtle)]">Answered questions, not an ability score</p></div><div className="rounded-xl bg-[var(--color-raised)] p-4"><p className="text-xs text-[var(--color-muted)]">Suggested discussion topics</p><p className="mt-2 text-xs leading-5">{result.recommended_course_ids?.join(' · ')||'Discuss goals with a counselor'}</p></div></div><h4 className="mt-5 text-xs font-bold">Recommendation rationale</h4><p className="mt-2 text-xs leading-5 text-[var(--color-muted)]">{result.recommendation_rationale}</p><button onClick={reset} className="mt-5 inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2.5 text-xs font-semibold"><RotateCcw size={14}/> Start another assessment</button></section>
      <aside className={panel+' p-5'}><h3 className="text-sm font-bold">Interest profile</h3><div className="mt-4 space-y-3">{(result.dimension_scores||[]).map(d=><div key={d.dimension}><div className="mb-1 flex justify-between text-xs"><span className="capitalize">{d.dimension}</span><span>{d.points} selections</span></div><div className="h-2 overflow-hidden rounded-full bg-[var(--color-raised)]"><div className="h-full rounded-full bg-[var(--color-accent-strong)]" style={{width:Math.min(100,d.points/8*100)+'%'}}/></div></div>)}</div><p className="mt-5 text-xs leading-5 text-[var(--color-muted)]">Use this as a starting point for a conversation, not as a label for the learner.</p></aside>
    </div>}

    {error&&<div role="alert" className="rounded-xl border border-amber-300/20 bg-amber-300/[0.05] p-4 text-xs text-amber-100">{error}</div>}
    {notice&&assessment&&<p role="status" className="text-xs text-[var(--color-muted)]">{notice}</p>}
    <p className="text-[10px] leading-5 text-[var(--color-subtle)]">Data handling: live responses are saved against the selected lead in PostgreSQL. Demo responses remain in local component state and are not sent to the backend. No outbound message is sent by this assessment.</p>
  </div>;
}
