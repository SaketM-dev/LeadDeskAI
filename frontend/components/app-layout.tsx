'use client';

import { usePathname } from 'next/navigation';
import AppShell from '@/components/app-shell';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // The root route is a public marketing landing page; product routes use the workspace shell.
  if (pathname === '/') return <>{children}</>;
  return <AppShell>{children}</AppShell>;
}
