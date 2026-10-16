import type { Metadata } from 'next';
import './globals.css';
import { DEMO_MODE } from '@/lib/mode';

export const metadata: Metadata = {
  title: 'AI Lead Desk | Admissions & Counseling Platform',
  description: 'AI-assisted admissions lead management and counseling platform for education institutes.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>
    {DEMO_MODE && <div className="sticky top-0 z-50 flex items-center justify-between border-b border-purple-300 bg-purple-100 px-4 py-2 text-xs font-semibold text-purple-900"><span>DEMO MODE — displaying fictional fixtures; no external messages or bookings are made.</span><span>SIMULATED</span></div>}
    {children}
  </body></html>;
}
