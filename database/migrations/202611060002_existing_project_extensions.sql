-- Extend the existing AI Lead Desk Supabase tables for the current backend.
-- Apply after 20261018_production_schema_compat.sql and
-- 20261017_admissions_workflows.sql. Preserves existing lead/course rows.
BEGIN;

-- The connected project has a legacy course catalogue. Keep its original
-- columns, copy values into the current API contract, and leave every course
-- unapproved unless it was already explicitly approved with a timestamp.
ALTER TABLE public.courses
  ADD COLUMN IF NOT EXISTS code text,
  ADD COLUMN IF NOT EXISTS title text,
  ADD COLUMN IF NOT EXISTS fee_amount numeric(12,2),
  ADD COLUMN IF NOT EXISTS fee_currency char(3) DEFAULT 'INR',
  ADD COLUMN IF NOT EXISTS fee_basis text,
  ADD COLUMN IF NOT EXISTS fee_verified boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS duration_weeks integer,
  ADD COLUMN IF NOT EXISTS schedule_text text,
  ADD COLUMN IF NOT EXISTS schedule_timezone text NOT NULL DEFAULT 'Asia/Kolkata',
  ADD COLUMN IF NOT EXISTS eligibility_text text,
  ADD COLUMN IF NOT EXISTS discount_policy_text text,
  ADD COLUMN IF NOT EXISTS placement_claim_text text,
  ADD COLUMN IF NOT EXISTS start_date date,
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'draft',
  ADD COLUMN IF NOT EXISTS approved_at timestamptz,
  ADD COLUMN IF NOT EXISTS content_updated_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

UPDATE public.courses
SET code = COALESCE(code, 'legacy-' || left(id::text, 8)),
    title = COALESCE(title, name),
    fee_amount = COALESCE(fee_amount, fee),
    fee_currency = COALESCE(fee_currency, 'INR'),
    fee_verified = COALESCE(fee_verified, false),
    schedule_text = COALESCE(schedule_text, schedule),
    schedule_timezone = COALESCE(schedule_timezone, 'Asia/Kolkata'),
    status = CASE WHEN status = 'approved' AND approved_at IS NOT NULL THEN 'approved' ELSE 'draft' END,
    content_updated_at = COALESCE(content_updated_at, updated_at, now()),
    metadata = COALESCE(metadata, '{}'::jsonb);

ALTER TABLE public.courses
  ALTER COLUMN code SET NOT NULL,
  ALTER COLUMN title SET NOT NULL,
  ALTER COLUMN fee_currency SET DEFAULT 'INR',
  ALTER COLUMN status SET DEFAULT 'draft';

CREATE UNIQUE INDEX IF NOT EXISTS courses_code_current_api_idx ON public.courses(code);
CREATE INDEX IF NOT EXISTS courses_status_title_current_api_idx ON public.courses(status, title);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.courses'::regclass
      AND conname = 'courses_status_current_api_check'
  ) THEN
    ALTER TABLE public.courses
      ADD CONSTRAINT courses_status_current_api_check
      CHECK (status IN ('draft','approved','inactive','draft_demo_only'));
  END IF;
END $$;

-- Current dashboard code reads app_users.full_name; the workflow migration
-- names the same field display_name. Keep both names for compatibility.
ALTER TABLE public.app_users ADD COLUMN IF NOT EXISTS full_name text;
UPDATE public.app_users SET full_name = COALESCE(full_name, display_name, email);

-- Add the current API's assessment fields to the workflow table. Existing
-- answers/results columns from the earlier design remain intact.
ALTER TABLE public.aptitude_assessments
  ADD COLUMN IF NOT EXISTS language text NOT NULL DEFAULT 'en',
  ADD COLUMN IF NOT EXISTS goal_summary text,
  ADD COLUMN IF NOT EXISTS score numeric(5,2),
  ADD COLUMN IF NOT EXISTS result_summary text,
  ADD COLUMN IF NOT EXISTS recommended_course_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS recommendation_rationale text,
  ADD COLUMN IF NOT EXISTS started_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS completed_at timestamptz;

CREATE TABLE IF NOT EXISTS public.aptitude_questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  question_key text NOT NULL,
  version integer NOT NULL DEFAULT 1,
  question_text jsonb NOT NULL,
  options jsonb NOT NULL,
  scoring_rubric jsonb NOT NULL,
  skill_dimension text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(question_key, version)
);

CREATE TABLE IF NOT EXISTS public.aptitude_responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id uuid NOT NULL REFERENCES public.aptitude_assessments(id) ON DELETE CASCADE,
  question_id uuid NOT NULL REFERENCES public.aptitude_questions(id) ON DELETE RESTRICT,
  answer_text text,
  selected_option_key text,
  score_awarded numeric(6,2) NOT NULL DEFAULT 0,
  max_score numeric(6,2) NOT NULL DEFAULT 0,
  response_order integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(assessment_id, question_id),
  UNIQUE(assessment_id, response_order)
);

CREATE TABLE IF NOT EXISTS public.lead_identities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  channel text NOT NULL CHECK (channel IN ('whatsapp','instagram','phone_call','website_form','email','walk_in','manual','other')),
  provider_contact_id text,
  phone_e164 text,
  email_normalized text,
  display_name text,
  identity_status text NOT NULL DEFAULT 'candidate' CHECK (identity_status IN ('candidate','verified','rejected')),
  verification_method text,
  created_at timestamptz NOT NULL DEFAULT now(),
  verified_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_identity_channel_provider_current_api_idx
  ON public.lead_identities(channel, provider_contact_id) WHERE provider_contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_identity_phone_current_api_idx
  ON public.lead_identities(phone_e164) WHERE phone_e164 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_identity_email_current_api_idx
  ON public.lead_identities(email_normalized) WHERE email_normalized IS NOT NULL;

ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS external_thread_id text;
CREATE UNIQUE INDEX IF NOT EXISTS uq_conversations_channel_thread_lead_current_api_idx
  ON public.conversations(channel, external_thread_id, lead_id)
  WHERE external_thread_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.lead_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  actor_user_id uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  channel text,
  related_entity_type text,
  related_entity_id uuid,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lead_events_timeline_current_api_idx
  ON public.lead_events(lead_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  direction text NOT NULL CHECK (direction IN ('inbound','outbound','internal')),
  sender_type text NOT NULL CHECK (sender_type IN ('prospect','ai','counselor','system','provider')),
  external_message_id text,
  body_text text,
  detected_language text,
  created_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.knowledge_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  logical_key text NOT NULL,
  version integer NOT NULL CHECK (version > 0),
  title text NOT NULL,
  document_type text NOT NULL,
  content text NOT NULL,
  status text NOT NULL DEFAULT 'draft',
  valid_from timestamptz,
  valid_until timestamptz,
  approved_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  approved_at timestamptz,
  updated_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  content_hash text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(logical_key, version)
);

CREATE TABLE IF NOT EXISTS public.lead_objections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  message_id uuid REFERENCES public.messages(id) ON DELETE SET NULL,
  objection_type text NOT NULL,
  evidence_text text,
  confidence numeric(4,3),
  status text NOT NULL DEFAULT 'open',
  detected_by text NOT NULL DEFAULT 'ai',
  created_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);

CREATE TABLE IF NOT EXISTS public.demo_slots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id uuid REFERENCES public.courses(id) ON DELETE SET NULL,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  timezone text NOT NULL DEFAULT 'Asia/Kolkata',
  capacity integer NOT NULL DEFAULT 1 CHECK (capacity > 0),
  status text NOT NULL DEFAULT 'open',
  provider text NOT NULL DEFAULT 'mock',
  provider_event_id text,
  provider_mode text NOT NULL DEFAULT 'simulated',
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (ends_at > starts_at)
);

CREATE TABLE IF NOT EXISTS public.lead_score_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  old_score smallint,
  new_score smallint NOT NULL,
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  model_or_rule_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.provider_webhook_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  provider_event_id text NOT NULL,
  event_type text NOT NULL,
  signature_valid boolean NOT NULL DEFAULT false,
  processing_status text NOT NULL DEFAULT 'received',
  payload jsonb NOT NULL,
  error_message text,
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  UNIQUE(provider, provider_event_id)
);

CREATE TABLE IF NOT EXISTS public.lead_source_touches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  source text NOT NULL,
  campaign text,
  landing_page text,
  external_click_id text,
  touched_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

COMMIT;
