export type UUID = string;
export type ISOTimestamp = string;
export type Language = 'en' | 'hi' | 'mr' | 'mixed' | string;
export type LeadStage = 'new' | 'contacted' | 'qualified' | 'demo_booked' | 'demo_attended' | 'nurturing' | 'admitted' | 'lost' | 'do_not_contact';
export type LeadSource = 'whatsapp' | 'instagram' | 'phone_call' | 'website_form' | 'email' | 'walk_in' | 'manual' | 'other';
export interface ApiList<T> { data: T[]; page?: { next_cursor: string | null }; }
export interface ApiErrorBody { error: { code: string; message: string; request_id?: string; details?: unknown[] }; }
export interface Lead {
  id: UUID;
  full_name: string;
  preferred_language?: Language;
  source: LeadSource;
  stage: LeadStage;
  lead_score: number;
  assigned_to?: UUID | null;
  created_at?: ISOTimestamp;
  updated_at?: ISOTimestamp;
}
export interface CreateLeadInput {
  full_name: string;
  phone?: string;
  email?: string;
  preferred_language?: Language;
  source: LeadSource;
  notes?: string;
  consent?: Record<string, boolean>;
}
export interface DashboardSummary {
  stage_counts: Partial<Record<LeadStage, number>>;
  overdue_follow_ups: number;
  new_leads: number;
  unassigned_leads: number;
}


export type ObjectionType = 'fees' | 'job_fears' | 'family_approval' | 'time' | 'eligibility' | 'location' | 'trust' | 'other';
export type TimelineEventType = 'message' | 'stage_change' | 'note' | 'follow_up' | 'booking' | 'handoff';
export interface LeadObjection {
  type: ObjectionType;
  label: string;
  evidence?: string;
  detected_at?: ISOTimestamp;
}
export interface LeadTimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description: string;
  occurred_at: ISOTimestamp;
  channel?: string;
  actor?: string;
}
export interface LeadDetail extends Lead {
  conversation_id?: UUID;
  phone?: string;
  email?: string;
  course_interest?: string;
  summary: string[];
  objections: LeadObjection[];
  next_action: string;
  consent: Record<string, boolean>;
  human_takeover: boolean;
  assigned_name?: string;
  timeline: LeadTimelineEvent[];
}
export interface CreateLeadNoteInput { text: string; }
export interface CreateFollowUpInput {
  lead_id: UUID;
  channel: string;
  action_type: string;
  reason: string;
  suggested_message?: string;
  scheduled_at?: ISOTimestamp;
  priority?: 'low' | 'normal' | 'high';
}
