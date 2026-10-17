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
const DEMO_QUESTIONS: { question: Record<string,string>; options: Option[] }[] = [
  { question: {en:'Which kind of activity do you enjoy most?',hi:'आपको किस तरह की गतिविधि सबसे अधिक पसंद है?',mr:'तुम्हाला कोणती कृती सर्वाधिक आवडते?'}, options:[
    {key:'data',label:{en:'Finding patterns in data',hi:'डेटा में पैटर्न खोजना',mr:'डेटामधील पॅटर्न शोधणे'}},
    {key:'software',label:{en:'Building apps and solving technical problems',hi:'ऐप बनाना और तकनीकी समस्याएँ हल करना',mr:'अॅप तयार करणे आणि तांत्रिक समस्या सोडवणे'}},
    {key:'design',label:{en:'Creative design and understanding users',hi:'रचनात्मक डिज़ाइन और उपयोगकर्ताओं को समझना',mr:'क्रिएटिव्ह डिझाइन आणि वापरकर्त्यांना समजून घेणे'}},
    {key:'business',label:{en:'Planning, communication and leadership',hi:'योजना, संवाद और नेतृत्व',mr:'नियोजन, संवाद आणि नेतृत्व'}},
  ]},
  { question: {en:'Which problem would you prefer to explore?',hi:'आप किस समस्या को समझना चाहेंगे?',mr:'तुम्हाला कोणती समस्या समजून घ्यायला आवडेल?'}, options:[
    {key:'data',label:{en:'Why a trend appears in a dataset',hi:'डेटासेट में कोई रुझान क्यों दिखता है',mr:'डेटासेटमध्ये एखादा कल का दिसतो'}},
    {key:'software',label:{en:'How to make an app work reliably',hi:'ऐप को भरोसेमंद तरीके से कैसे चलाएँ',mr:'अॅप विश्वासार्हपणे कसे चालवावे'}},
    {key:'ai',label:{en:'How an AI model makes a prediction',hi:'AI मॉडल भविष्यवाणी कैसे करता है',mr:'AI मॉडेल अंदाज कसा लावते'}},
    {key:'design',label:{en:'Why people find an interface confusing',hi:'लोगों को इंटरफ़ेस उलझाऊ क्यों लगता है',mr:'लोकांना इंटरफेस गोंधळात टाकणारा का वाटतो'}},
  ]},
  { question: {en:'Which output would you most enjoy creating?',hi:'आपको इनमें से क्या बनाना पसंद होगा?',mr:'यापैकी काय तयार करायला आवडेल?'}, options:[
    {key:'data',label:{en:'A clear chart backed by evidence',hi:'डेटा पर आधारित स्पष्ट चार्ट',mr:'पुराव्यावर आधारित स्पष्ट चार्ट'}},
    {key:'software',label:{en:'A useful working web application',hi:'एक उपयोगी वेब ऐप',mr:'उपयुक्त वेब अॅप'}},
    {key:'design',label:{en:'A prototype that is easy to use',hi:'आसानी से इस्तेमाल होने वाला प्रोटोटाइप',mr:'सहज वापरता येणारा प्रोटोटाइप'}},
    {key:'business',label:{en:'A product plan that solves a customer need',hi:'ग्राहक की जरूरत हल करने वाली उत्पाद योजना',mr:'ग्राहकाची गरज सोडवणारी उत्पादन योजना'}},
  ]},
  { question: {en:'Which skill would you most like to practise?',hi:'आप किस कौशल का अभ्यास करना चाहेंगे?',mr:'तुम्हाला कोणत्या कौशल्याचा सराव करायला आवडेल?'}, options:[
    {key:'data',label:{en:'Statistics and analytical thinking',hi:'सांख्यिकी और विश्लेषणात्मक सोच',mr:'सांख्यिकी आणि विश्लेषणात्मक विचार'}},
    {key:'software',label:{en:'Programming and debugging',hi:'प्रोग्रामिंग और डिबगिंग',mr:'प्रोग्रामिंग आणि डीबगिंग'}},
    {key:'ai',label:{en:'Experimenting with AI models',hi:'AI मॉडल के साथ प्रयोग',mr:'AI मॉडेल्ससोबत प्रयोग'}},
    {key:'design',label:{en:'User research and visual communication',hi:'उपयोगकर्ता शोध और दृश्य संचार',mr:'वापरकर्ता संशोधन आणि दृश्य संवाद'}},
  ]},
  { question: {en:'When learning something new, what motivates you?',hi:'कुछ नया सीखते समय आपको क्या प्रेरित करता है?',mr:'नवीन शिकताना तुम्हाला कशामुळे प्रेरणा मिळते?'}, options:[
    {key:'data',label:{en:'Explaining evidence and patterns',hi:'सबूत और पैटर्न समझाना',mr:'पुरावे आणि पॅटर्न समजावणे'}},
    {key:'software',label:{en:'Making a solution work end to end',hi:'समाधान को शुरू से अंत तक काम करते देखना',mr:'संपूर्ण उपाय कार्यरत करणे'}},
    {key:'business',label:{en:'Organising people and decisions',hi:'लोगों और निर्णयों को व्यवस्थित करना',mr:'लोक आणि निर्णयांचे नियोजन करणे'}},
    {key:'design',label:{en:'Making an experience clearer for people',hi:'लोगों के लिए अनुभव को आसान बनाना',mr:'लोकांसाठी अनुभव अधिक सोपा करणे'}},
  ]},
  { question: {en:'Which topic would you choose for a small project?',hi:'छोटी परियोजना के लिए आप कौन-सा विषय चुनेंगे?',mr:'लहान प्रकल्पासाठी तुम्ही कोणता विषय निवडाल?'}, options:[
    {key:'data',label:{en:'Explore and visualise a dataset',hi:'डेटासेट का विश्लेषण और दृश्यांकन',mr:'डेटासेटचा अभ्यास आणि दृश्यांकन'}},
    {key:'software',label:{en:'Build a simple website or app',hi:'एक सरल वेबसाइट या ऐप बनाना',mr:'साधी वेबसाइट किंवा अॅप तयार करणे'}},
    {key:'ai',label:{en:'Test an AI tool and review its limits',hi:'AI टूल को परखना और उसकी सीमाएँ देखना',mr:'AI साधन तपासणे आणि त्याच्या मर्यादा पाहणे'}},
    {key:'business',label:{en:'Research a customer problem and pitch a solution',hi:'ग्राहक की समस्या समझकर समाधान प्रस्तुत करना',mr:'ग्राहकाची समस्या समजून उपाय मांडणे'}},
  ]},
  { question: {en:'What kind of feedback do you like receiving?',hi:'आप किस तरह की प्रतिक्रिया पसंद करते हैं?',mr:'तुम्हाला कोणता अभिप्राय आवडतो?'}, options:[
    {key:'data',label:{en:'Whether conclusions match the evidence',hi:'क्या निष्कर्ष सबूतों से मेल खाते हैं',mr:'निष्कर्ष पुराव्यांशी जुळतात का'}},
    {key:'software',label:{en:'Whether a solution works reliably',hi:'क्या समाधान भरोसेमंद है',mr:'उपाय विश्वासार्ह आहे का'}},
    {key:'design',label:{en:'Whether people can use it comfortably',hi:'क्या लोग इसे आसानी से इस्तेमाल कर सकते हैं',mr:'लोक ते सहज वापरू शकतात का'}},
    {key:'business',label:{en:'Whether it solves the right problem',hi:'क्या यह सही समस्या हल करता है',mr:'तो योग्य समस्या सोडवतो का'}},
  ]},
  { question: {en:'What would you like to learn more about next?',hi:'आप आगे किस बारे में सीखना चाहेंगे?',mr:'पुढे तुम्हाला कशाबद्दल अधिक शिकायला आवडेल?'}, options:[
    {key:'data',label:{en:'Data analysis and visualisation',hi:'डेटा विश्लेषण और दृश्यांकन',mr:'डेटा विश्लेषण आणि दृश्यांकन'}},
    {key:'software',label:{en:'Web development and APIs',hi:'वेब डेवलपमेंट और APIs',mr:'वेब डेव्हलपमेंट आणि APIs'}},
    {key:'ai',label:{en:'AI and machine learning',hi:'AI और मशीन लर्निंग',mr:'AI आणि मशीन लर्निंग'}},
    {key:'design',label:{en:'UI/UX and product design',hi:'UI/UX और उत्पाद डिज़ाइन',mr:'UI/UX आणि उत्पादन डिझाइन'}},
  ]},
];

const COURSE_BY_DIMENSION: Record<string,string> = {
  data:'Data Science with Python', software:'Full-Stack Web Development',
  ai:'AI & Machine Learning Foundations', design:'UI/UX Design Fundamentals',
  business:'Business and Product Strategy',
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
      <div className="max-w-2xl"><div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-accent)]"><ClipboardCheck size={16}/> INTEREST-LED ASSESSMENT <span className={'rounded-full px-2 py-1 text-[10px] '+(demoModeActive?'bg-[var(--color-warning-soft)] text-[var(--color-warning)]':'bg-[var(--color-success-soft)] text-[var(--color-success)]')}>{demoModeActive?'DEMO · LOCAL ONLY':'LIVE · PERSISTED'}</span></div><h2 className="mt-3 text-xl font-bold">Discover learning preferences</h2><p className="mt-2 text-xs leading-5 text-[var(--color-muted)]">Eight short questions explore interests across data, software, AI, design and business. Results are saved for live assessments and are intended only to support a counselor conversation.</p></div>
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
        <div className="flex items-center justify-between gap-3"><span className="text-xs font-semibold text-[var(--color-muted)]">Question {index+1} of 8</span><span className="text-xs text-[var(--color-subtle)]">{Math.round((selectedCount/8)*100)}% answered</span></div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--color-raised)]"><div className="h-full rounded-full bg-[var(--color-accent-strong)] transition-all" style={{width:(selectedCount/8*100)+'%'}}/></div>
        <h3 className="mt-6 text-lg font-bold leading-7">{displayQuestion}</h3>
        <p className="mt-2 text-xs text-[var(--color-muted)]">{language==='hi'?'वह विकल्प चुनें जो आपकी रुचि को सबसे अच्छी तरह दर्शाता है।':language==='mr'?'तुमची आवड सर्वात चांगल्या प्रकारे दर्शवणारा पर्याय निवडा.':'Choose the option that best reflects the learner’s interests. There are no right or wrong answers.'}</p>
        <div className="mt-5 space-y-3">{current.options.map(o=><button key={o.key} disabled={loading||Boolean(selected[current.id])&&!demoModeActive} onClick={()=>choose(o.key)} className={'flex w-full items-center gap-3 rounded-xl border p-4 text-left text-xs transition '+(selected[current.id]===o.key?'border-[var(--color-accent)] bg-[var(--color-accent-soft)] text-[var(--color-accent)]':'border-[var(--color-border)] hover:border-[var(--color-accent)]')+' disabled:cursor-not-allowed disabled:opacity-70'}><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-current">{selected[current.id]===o.key&&<Check size={12}/>}</span>{label(o.label,language)}</button>)}</div>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3"><button disabled={index===0||loading} onClick={()=>setIndex(i=>i-1)} className="inline-flex items-center gap-1 rounded-lg border border-[var(--color-border)] px-4 py-2.5 text-xs disabled:opacity-40"><ChevronLeft size={14}/> Previous</button>{index<7?<button disabled={!selected[current.id]||loading} onClick={()=>{if(index<questions.length-1)setIndex(i=>i+1)}} className="inline-flex items-center gap-1 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-40">Next question <ChevronRight size={14}/></button>:<button disabled={selectedCount<8||loading} onClick={finish} className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent-strong)] px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-40">{loading?<LoaderCircle size={14} className="animate-spin"/>:<CheckCircle2 size={14}/>} Complete and save</button>}</div>
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
