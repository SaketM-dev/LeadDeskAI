import { apiFetch, ApiRequestError } from '@/lib/api-client';
import { DEMO_MODE } from '@/lib/mode';
import { demoLeads } from '@/fixtures/leads';
import type { ApiList, CreateLeadInput, Lead, LeadStage } from '@/types/api';

export interface LeadFilters { q?: string; stage?: LeadStage; source?: string; assigned_to?: string; min_score?: number; limit?: number; cursor?: string; }
function buildQuery(filters: LeadFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value !== undefined && value !== '') params.set(key, String(value)); });
  const query = params.toString();
  return query ? `?${query}` : '';
}
export async function listLeads(filters: LeadFilters = {}): Promise<Lead[]> {
  if (DEMO_MODE) {
    const query = (filters.q || '').toLowerCase();
    return demoLeads.filter(lead => (!query || lead.full_name.toLowerCase().includes(query)) && (!filters.stage || lead.stage === filters.stage) && (!filters.source || lead.source === filters.source) && (filters.min_score === undefined || lead.lead_score >= filters.min_score));
  }
  const response = await apiFetch<ApiList<Lead>>(`/leads${buildQuery(filters)}`);
  return response.data;
}
export async function createLead(input: CreateLeadInput): Promise<Lead> {
  if (DEMO_MODE) throw new ApiRequestError('Creating a lead through the API is disabled in demo mode. Demo UI records are local-only.', 0, 'DEMO_MODE');
  return apiFetch<Lead>('/leads', { method: 'POST', body: JSON.stringify(input) });
}
export async function updateLeadStage(leadId: string, stage: LeadStage): Promise<Lead> {
  if (DEMO_MODE) throw new ApiRequestError('Updating a lead through the API is disabled in demo mode.', 0, 'DEMO_MODE');
  return apiFetch<Lead>(`/leads/${encodeURIComponent(leadId)}`, { method: 'PATCH', body: JSON.stringify({ stage }) });
}
