import { apiFetch } from '@/lib/api-client';
import { DEMO_MODE } from '@/lib/mode';
import type { DashboardSummary } from '@/types/api';

export async function getDashboardSummary(): Promise<DashboardSummary> {
  if (DEMO_MODE) return {
    stage_counts: { new: 32, contacted: 46, qualified: 86, demo_booked: 18, nurturing: 24, admitted: 12 },
    overdue_follow_ups: 12,
    new_leads: 32,
    unassigned_leads: 7,
  };
  return apiFetch<DashboardSummary>('/dashboard/summary');
}
