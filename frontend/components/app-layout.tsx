'use client';

import { usePathname } from 'next/navigation';
import AppShell from '@/components/app-shell';
import GlobalChatbot from '@/components/global-chatbot';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // The chat assistant is available on public and workspace pages alike.
  return <>
    {pathname === '/' ? children : <AppShell>{children}</AppShell>}
    <GlobalChatbot />
  </>;
}
