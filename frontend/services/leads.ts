import { apiFetch, ApiRequestError } from '@/lib/api-client';
import { DEMO_MODE } from '@/lib/mode';
import { demoLeads } from '@/fixtures/leads';
import type {
  ApiList,
  CreateLeadInput,
  Lead,
  LeadDetail,
  LeadStage,
  LeadTimelineEvent,
  CreateFollowUpInput,
  LeadSource,
} from '@/types/api';

export interface LeadFilters {
  q?: string;
  stage?: LeadStage;
  source?: string;
  assigned_to?: string;
  min_score?: number;
  limit?: number;
  cursor?: string;
}

type ExistingBackendLead = {
  id: string;
  full_name: string;
  preferred_language?: string | null;
  stage?: string | null;
  lead_score?: number | null;
  three_line_summary?: string | null;
  assigned_user_id?: string | null;
  first_touch_source?: string | null;
  last_touch_source?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

type ExistingBackendLeadResponse = {
  count: number;
  leads: ExistingBackendLead[];
};

const supportedStages = new Set<LeadStage>([
  'new', 'contacted', 'qualified', 'demo_booked', 'demo_attended',
  'nurturing', 'admitted', 'lost', 'do_not_contact',
]);

function normalizeStage(value?: string | null): LeadStage {
  return value && supportedStages.has(value as LeadStage) ? value as LeadStage : 'new';
}

function normalizeSource(value?: string | null): LeadSource {
  const supported: LeadSource[] = [
    'whatsapp', 'instagram', 'phone_call', 'website_form', 'email',
    'walk_in', 'manual', 'other',
  ];
  return value && supported.includes(value as LeadSource) ? value as LeadSource : 'other';
}

function normalizeBackendLead(item: ExistingBackendLead): Lead {
  return {
    id: item.id,
    full_name: item.full_name,
    preferred_language: item.preferred_language || 'unknown',
    stage: normalizeStage(item.stage),
    lead_score: typeof item.lead_score === 'number' ? item.lead_score : 0,
    summary: item.three_line_summary ?? undefined,
    assigned_to: item.assigned_user_id ?? null,
    source: normalizeSource(item.first_touch_source),
    created_at: item.created_at ?? undefined,
    updated_at: item.updated_at ?? undefined,
  };
}

function applyFilters(leads: Lead[], filters: LeadFilters): Lead[] {
  const query = filters.q?.trim().toLowerCase();
  return leads.filter(lead =>
    (!query || lead.full_name.toLowerCase().includes(query) || lead.id.toLowerCase().includes(query)) &&
    (!filters.stage || lead.stage === filters.stage) &&
    (!filters.source || lead.source === filters.source) &&
    (!filters.assigned_to || lead.assigned_to === filters.assigned_to) &&
    (filters.min_score === undefined || lead.lead_score >= filters.min_score)
  ).slice(0, filters.limit ?? leads.length);
}

function unavailable(endpoint: string): ApiRequestError {
  return new ApiRequestError(
    `The current FastAPI backend does not implement ${endpoint} yet. This action has not been sent or saved.`,
    501,
    'BACKEND_ENDPOINT_UNAVAILABLE',
  );
}

export async function listLeads(filters: LeadFilters = {}): Promise<Lead[]> {
  if (DEMO_MODE) {
    const query = (filters.q || '').toLowerCase();
    return applyFilters(demoLeads.filter(lead =>
      (!query || lead.full_name.toLowerCase().includes(query)) &&
      (!filters.stage || lead.stage === filters.stage) &&
      (!filters.source || lead.source === filters.source) &&
      (filters.min_score === undefined || lead.lead_score >= filters.min_score)
    ), filters);
  }

  // The checked backend currently exposes GET /api/leads and returns
  // { count, leads }, rather than the planned /api/v1 list envelope.
  const response = await apiFetch<ExistingBackendLeadResponse>('/leads');
  if (!Array.isArray(response.leads)) {
    throw new ApiRequestError('Unexpected response from GET /api/leads.', 502, 'INVALID_API_RESPONSE');
  }
  return applyFilters(response.leads.map(normalizeBackendLead), filters);
}

export async function createLead(input: CreateLeadInput): Promise<Lead> {
  if (DEMO_MODE) throw new ApiRequestError('Creating a lead through the API is disabled in demo mode. Demo records are local-only.', 0, 'DEMO_MODE');

  // The current backend schema does not persist phone, email, or notes on lead
  // creation. Reject these explicitly rather than silently discarding user input.
  if (input.phone?.trim() || input.email?.trim() || input.notes?.trim()) {
    throw new ApiRequestError(
      'The live API currently supports name, language, source, and consent only. Phone, email, and notes were not saved.',
      422,
      'UNSUPPORTED_LEAD_FIELDS',
    );
  }

  const consent = input.consent ?? {};
  const response = await apiFetch<{ data: ExistingBackendLead }>('/v1/leads', {
    method: 'POST',
    body: JSON.stringify({
      full_name: input.full_name,
      preferred_language: input.preferred_language || 'unknown',
      source: input.source,
      marketing_consent: consent.marketing ?? false,
      whatsapp_consent: consent.whatsapp ?? false,
      email_consent: consent.email ?? false,
    }),
  });
  if (!response?.data?.id || !response.data.full_name) {
    throw new ApiRequestError('Unexpected response from POST /api/v1/leads.', 502, 'INVALID_API_RESPONSE');
  }
  return normalizeBackendLead(response.data);
}

export async function updateLeadStage(leadId: string, stage: LeadStage): Promise<Lead> {
  if (DEMO_MODE) throw new ApiRequestError('Updating a lead through the API is disabled in demo mode.', 0, 'DEMO_MODE');
  const response = await apiFetch<{ data: ExistingBackendLead }>(`/v1/leads/${encodeURIComponent(leadId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ stage }),
  });
  if (!response?.data?.id) {
    throw new ApiRequestError('Unexpected response from PATCH /api/v1/leads/{lead_id}.', 502, 'INVALID_API_RESPONSE');
  }
  return normalizeBackendLead(response.data);
}

export async function getLeadDetail(leadId: string): Promise<LeadDetail> {
  if (DEMO_MODE) {
    throw new ApiRequestError('Lead details are supplied by local demo fixtures while demo mode is enabled.', 0, 'DEMO_MODE');
  }

  // Fetch the authoritative record for this profile instead of guessing from
  // the first 100 items in the lead-list response.
  const response = await apiFetch<Partial<LeadDetail> & {
    id: string;
    full_name: string;
    stage?: string | null;
    lead_score?: number | null;
    source?: string | null;
    preferred_language?: string | null;
    summary?: string[] | null;
    objections?: LeadDetail['objections'] | null;
    consent?: Record<string, boolean> | null;
    timeline?: LeadTimelineEvent[] | null;
  }>(`/leads/${encodeURIComponent(leadId)}`);

  if (!response || response.id !== leadId || !response.full_name) {
    throw new ApiRequestError('Unexpected response from GET /api/leads/{lead_id}.', 502, 'INVALID_API_RESPONSE');
  }

  return {
    id: response.id,
    full_name: response.full_name,
    preferred_language: response.preferred_language || 'unknown',
    stage: normalizeStage(response.stage),
    lead_score: typeof response.lead_score === 'number' ? response.lead_score : 0,
    assigned_to: response.assigned_to ?? null,
    assigned_name: response.assigned_name ?? undefined,
    source: normalizeSource(response.source),
    created_at: response.created_at ?? undefined,
    updated_at: response.updated_at ?? undefined,
    phone: response.phone ?? undefined,
    email: response.email ?? undefined,
    course_interest: response.course_interest ?? undefined,
    summary: Array.isArray(response.summary) ? response.summary : [],
    objections: Array.isArray(response.objections) ? response.objections : [],
    next_action: response.next_action || 'Review the recorded lead details and confirm course interest with the learner.',
    consent: response.consent ?? {},
    human_takeover: response.human_takeover ?? false,
    conversation_id: response.conversation_id,
    timeline: Array.isArray(response.timeline) ? response.timeline : [],
  };
}

export async function addLeadNote(leadId: string, text: string): Promise<void> {
  if (DEMO_MODE) throw new ApiRequestError('Live notes are disabled in demo mode.', 0, 'DEMO_MODE');
  await apiFetch<{ data: { id: string } }>(`/v1/leads/${encodeURIComponent(leadId)}/notes`, {
    method: 'POST',
    body: JSON.stringify({ body: text }),
  });
}

export async function handoffLead(_leadId: string, _reason: 'human_requested' | 'low_confidence' | 'sensitive' | 'other' = 'human_requested'): Promise<void> {
  if (DEMO_MODE) throw new ApiRequestError('Live human handoff is disabled in demo mode.', 0, 'DEMO_MODE');
  throw unavailable('POST /api/leads/{lead_id}/handoff');
}

export async function releaseLeadToAI(_conversationId: string): Promise<void> {
  if (DEMO_MODE) throw new ApiRequestError('Live AI release is disabled in demo mode.', 0, 'DEMO_MODE');
  throw unavailable('POST /api/conversations/{conversation_id}/release-to-ai');
}

export async function createFollowUp(_input: CreateFollowUpInput): Promise<unknown> {
  if (DEMO_MODE) throw new ApiRequestError('Live follow-up creation is disabled in demo mode.', 0, 'DEMO_MODE');
  throw unavailable('POST /api/follow-ups');
}
