'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { Bot, LoaderCircle, MessageCircle, Send, X } from 'lucide-react';

type Message = { role: 'user' | 'assistant'; content: string };

const welcome: Message = {
  role: 'assistant',
  content: 'Hello! नमस्कार! नमस्कार! Ask me about courses or admissions in English, Hindi, Marathi, or a mix of languages.',
};

export default function GlobalChatbot() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([welcome]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, loading, open]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    const next: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setInput('');
    setError('');
    setLoading(true);
    try {
      const response = await fetch('/backend-api/chatbot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: next.filter((m, i) => !(i === 0 && m === welcome)).slice(-16) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || 'The chatbot could not respond. Please try again.');
      setMessages(current => [...current, { role: 'assistant', content: String(data.reply) }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return <div className="fixed bottom-5 right-5 z-[70] flex flex-col items-end">
    {open && <section aria-label="LeadDeskAI multilingual assistant" className="mb-3 flex h-[min(640px,calc(100dvh-112px))] w-[min(390px,calc(100vw-24px))] flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl shadow-black/40">
      <header className="flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-raised)] px-4 py-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-400/15 text-violet-200"><Bot size={21}/></div>
        <div className="min-w-0 flex-1"><h2 className="text-sm font-semibold">LeadDesk AI</h2><p className="text-xs text-[var(--color-muted)]">English · हिन्दी · मराठी</p></div>
        <button type="button" onClick={() => setOpen(false)} aria-label="Close chatbot" className="rounded-lg p-2 text-[var(--color-muted)] hover:bg-white/5"><X size={18}/></button>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
        {messages.map((message, index) => <div key={index} className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
          <div className={`max-w-[88%] whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${message.role === 'user' ? 'rounded-br-md bg-violet-500 text-white' : 'rounded-bl-md bg-[var(--color-raised)] text-[var(--color-text)]'}`}>{message.content}</div>
        </div>)}
        {loading && <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]"><LoaderCircle size={15} className="animate-spin"/>Thinking…</div>}
        {error && <p role="alert" className="rounded-lg border border-amber-400/20 bg-amber-400/5 p-2 text-xs text-amber-200">{error}</p>}
        <div ref={endRef}/>
      </div>
      <form onSubmit={submit} className="border-t border-[var(--color-border)] p-3">
        <label className="sr-only" htmlFor="lead-desk-chat-input">Message the admissions assistant</label>
        <div className="flex items-end gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-page)] p-2">
          <textarea id="lead-desk-chat-input" rows={1} maxLength={6000} value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} placeholder="Ask in English, Hindi or Marathi…" className="max-h-28 min-h-10 flex-1 resize-y bg-transparent px-2 py-2 text-sm outline-none placeholder:text-[var(--color-subtle)]" />
          <button type="submit" disabled={!input.trim() || loading} aria-label="Send message" className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500 text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-40"><Send size={16}/></button>
        </div>
        <p className="mt-2 text-[10px] text-[var(--color-subtle)]">Course answers use approved institute information. Booking is not available in this chat yet.</p>
      </form>
    </section>}
    <button type="button" onClick={() => setOpen(value => !value)} aria-expanded={open} aria-label={open ? 'Close LeadDesk AI chat' : 'Open LeadDesk AI chat'} className="flex items-center gap-2 rounded-full border border-violet-300/20 bg-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-950/30 transition hover:bg-violet-500">
      {open ? <X size={18}/> : <MessageCircle size={19}/>}<span>{open ? 'Close chat' : 'Ask LeadDesk AI'}</span>
    </button>
  </div>;
}
