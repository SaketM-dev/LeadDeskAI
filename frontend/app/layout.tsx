import type { Metadata } from 'next';
import './globals.css';
import AppShell from '@/components/app-shell';

export const metadata: Metadata = {
  title: 'AI Lead Desk | Admissions Workspace',
  description: 'Admissions lead management, AI counselling, course recommendations, bookings and follow-up workspace.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><AppShell>{children}</AppShell></body></html>;
}
