import type { Metadata } from 'next';
import './globals.css';
import AppLayout from '@/components/app-layout';

export const metadata: Metadata = {
  title: 'AI Lead Desk | AI-powered admissions',
  description: 'One intelligent workspace for admissions teams: manage leads, guide students, and automate follow-ups.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><AppLayout>{children}</AppLayout></body></html>;
}
