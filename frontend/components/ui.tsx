import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export function Button({ variant = 'primary', className = '', type = 'button', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  const styles: Record<ButtonVariant, string> = {
    primary: 'bg-[var(--color-accent-strong)] text-white hover:bg-[var(--color-accent)]',
    secondary: 'border border-[var(--color-border)] bg-[var(--color-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface)]',
    danger: 'bg-[var(--color-danger-soft)] text-[var(--color-danger)] hover:brightness-110',
    ghost: 'text-[var(--color-muted)] hover:bg-[var(--color-raised)] hover:text-[var(--color-text)]',
  };
  return <button type={type} className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-[var(--radius-control)] px-4 py-2 text-sm font-semibold transition-colors duration-160 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)] disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`} {...props}/>;
}

export function Card({ children, className = '', title, description, action }: { children: ReactNode; className?: string; title?: string; description?: string; action?: ReactNode }) {
  return <section className={`rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)] ${className}`}>
    {(title || description || action) && <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--color-border)] px-5 py-4"><div>{title && <h2 className="text-sm font-semibold text-[var(--color-text)]">{title}</h2>}{description && <p className="mt-1 text-xs leading-5 text-[var(--color-muted)]">{description}</p>}</div>{action}</div>}
    <div className="p-5">{children}</div>
  </section>;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`ui-input text-sm ${props.className || ''}`}/>;
}
export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`ui-input text-sm ${props.className || ''}`}/>;
}
export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`ui-input text-sm ${props.className || ''}`}/>;
}

type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: BadgeTone }) {
  const tones: Record<BadgeTone, string> = {
    neutral: 'border-[var(--color-border)] bg-[var(--color-raised)] text-[var(--color-muted)]',
    success: 'border-[var(--color-success)]/30 bg-[var(--color-success-soft)] text-[var(--color-success)]',
    warning: 'border-[var(--color-warning)]/30 bg-[var(--color-warning-soft)] text-[var(--color-warning)]',
    danger: 'border-[var(--color-danger)]/30 bg-[var(--color-danger-soft)] text-[var(--color-danger)]',
    info: 'border-[var(--color-info)]/30 bg-[var(--color-info-soft)] text-[var(--color-info)]',
    purple: 'border-[var(--color-purple)]/30 bg-[var(--color-purple-soft)] text-[var(--color-purple)]',
  };
  return <span className={`ui-badge ${tones[tone]}`}>{children}</span>;
}

export function EmptyState({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) {
  return <div className="ui-empty rounded-xl border border-dashed border-[var(--color-border)]"><p className="font-semibold text-[var(--color-text)]">{title}</p>{detail && <p className="max-w-md text-xs leading-5">{detail}</p>}{action}</div>;
}
export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return <div role="status" aria-live="polite" className="flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-sm text-[var(--color-muted)]"><span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-accent)]"/>{label}</div>;
}
export function ErrorState({ title = 'Unable to load data', detail, onRetry }: { title?: string; detail: string; onRetry?: () => void }) {
  return <div role="alert" className="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger-soft)] p-4"><p className="text-sm font-semibold text-[var(--color-danger)]">{title}</p><p className="mt-1 text-xs leading-5 text-[var(--color-text)]">{detail}</p>{onRetry && <Button className="mt-3" variant="secondary" onClick={onRetry}>Try again</Button>}</div>;
}

export function Modal({ title, description, children, onClose }: { title: string; description?: string; children: ReactNode; onClose: () => void }) {
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section role="dialog" aria-modal="true" aria-labelledby="ui-modal-title" className="w-full max-w-lg rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-raised)]">
      <div className="flex items-start justify-between gap-4"><div><h2 id="ui-modal-title" className="text-lg font-semibold">{title}</h2>{description && <p className="mt-1 text-sm text-[var(--color-muted)]">{description}</p>}</div><Button variant="ghost" aria-label="Close dialog" onClick={onClose}>×</Button></div>
      <div className="mt-5">{children}</div>
    </section>
  </div>;
}
