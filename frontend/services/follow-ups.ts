import { apiFetch, ApiRequestError } from '@/lib/api-client';
import { DEMO_MODE } from '@/lib/mode';

export type FollowUpTask = {
  id: string;
  lead_id: string;
  title: string;
  suggested_message?: string | null;
  priority: 'low' | 'medium' | 'high';
  due_at: string;
  status: 'pending' | 'completed' | 'cancelled';
  completed_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

type ListResponse = { data: FollowUpTask[]; page?: { next_cursor?: string | null } };
type ItemResponse = { data: FollowUpTask };

function ensureLiveMode() {
  if (DEMO_MODE) {
    throw new ApiRequestError('Demo mode is enabled. Set NEXT_PUBLIC_DEMO_MODE=false and restart the frontend to use saved follow-ups.', 0, 'DEMO_MODE');
  }
}

export async function listFollowUps(): Promise<FollowUpTask[]> {
  ensureLiveMode();
  const response = await apiFetch<ListResponse>('/v1/follow-ups?limit=100');
  if (!Array.isArray(response.data)) {
    throw new ApiRequestError('Unexpected response from the follow-up API.', 502, 'INVALID_API_RESPONSE');
  }
  return response.data;
}

export async function createFollowUp(input: {
  lead_id: string; title: string; priority: FollowUpTask['priority']; due_at: string;
}): Promise<FollowUpTask> {
  ensureLiveMode();
  const response = await apiFetch<ItemResponse>('/v1/follow-ups', {
    method: 'POST', body: JSON.stringify(input),
  });
  return response.data;
}

export async function updateFollowUp(taskId: string, dueAt: string): Promise<FollowUpTask> {
  ensureLiveMode();
  const response = await apiFetch<ItemResponse>(`/v1/follow-ups/${encodeURIComponent(taskId)}`, {
    method: 'PATCH', body: JSON.stringify({ due_at: dueAt }),
  });
  return response.data;
}

export async function completeFollowUp(taskId: string): Promise<FollowUpTask> {
  ensureLiveMode();
  const response = await apiFetch<ItemResponse>(`/v1/follow-ups/${encodeURIComponent(taskId)}/complete`, {
    method: 'POST',
  });
  return response.data;
}
