-- AI Lead Desk PostgreSQL schema v1
-- All timestamps are timestamptz (UTC). Run as a versioned migration in deployment.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 full_name text NOT NULL, email text NOT NULL UNIQUE,
 role text NOT NULL CHECK (role IN ('admin','manager','counselor')),
 is_active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leads (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 full_name text NOT NULL, normalized_name text,
 preferred_language text CHECK (preferred_language IN ('en','hi','mr','mixed','unknown')) DEFAULT 'unknown',
 stage text NOT NULL DEFAULT 'new' CHECK (stage IN ('new','contacted','qualified','demo_booked','demo_attended','nurturing','admitted','lost','do_not_contact')),
 lead_score smallint NOT NULL DEFAULT 0 CHECK (lead_score BETWEEN 0 AND 100),
 score_reasons jsonb NOT NULL DEFAULT '[]'::jsonb, three_line_summary text,
 assigned_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
 first_touch_source text, last_touch_source text,
 marketing_consent boolean NOT NULL DEFAULT false, whatsapp_consent boolean NOT NULL DEFAULT false,
 email_consent boolean NOT NULL DEFAULT false, do_not_contact boolean NOT NULL DEFAULT false,
 last_inbound_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(), admitted_at timestamptz,
 merged_into_lead_id uuid REFERENCES leads(id) ON DELETE RESTRICT,
 CHECK (merged_into_lead_id IS NULL OR merged_into_lead_id <> id)
);
CREATE INDEX IF NOT EXISTS idx_leads_stage_updated ON leads(stage, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_assignee_score ON leads(assigned_user_id, lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_source_created ON leads(first_touch_source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_name_search ON leads USING gin (to_tsvector('simple', coalesce(full_name,'')));

CREATE TABLE IF NOT EXISTS lead_identities (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 channel text NOT NULL CHECK (channel IN ('whatsapp','instagram','phone_call','website_form','email','walk_in','manual','other')),
 provider_contact_id text, phone_e164 text, email_normalized text, display_name text,
 identity_status text NOT NULL DEFAULT 'candidate' CHECK (identity_status IN ('candidate','verified','rejected')),
 verification_method text, created_at timestamptz NOT NULL DEFAULT now(), verified_at timestamptz,
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_identity_channel_provider ON lead_identities(channel, provider_contact_id) WHERE provider_contact_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_identity_channel_phone ON lead_identities(channel, phone_e164) WHERE phone_e164 IS NOT NULL AND identity_status='verified';
CREATE INDEX IF NOT EXISTS idx_identity_phone ON lead_identities(phone_e164) WHERE phone_e164 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_identity_email ON lead_identities(email_normalized) WHERE email_normalized IS NOT NULL;

CREATE TABLE IF NOT EXISTS conversations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 channel text NOT NULL CHECK (channel IN ('whatsapp','instagram','phone_call','website_form','email','walk_in','manual','other')),
 external_thread_id text,
 status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','waiting_for_lead','waiting_for_counselor','closed')),
 ai_enabled boolean NOT NULL DEFAULT true, assigned_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
 last_message_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_conversation_external_thread ON conversations(channel, external_thread_id) WHERE external_thread_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_conversations_lead_last_msg ON conversations(lead_id, last_message_at DESC);

CREATE TABLE IF NOT EXISTS messages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 direction text NOT NULL CHECK (direction IN ('inbound','outbound','internal')),
 sender_type text NOT NULL CHECK (sender_type IN ('prospect','ai','counselor','system','provider')),
 external_message_id text, body_text text, detected_language text,
 media_type text CHECK (media_type IN ('audio','image','video','document','none')) DEFAULT 'none',
 media_url text, transcript_text text,
 delivery_status text CHECK (delivery_status IN ('queued','sent','delivered','read','failed','received')),
 sent_by_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
 knowledge_source_ids jsonb NOT NULL DEFAULT '[]'::jsonb, unsupported_claims jsonb NOT NULL DEFAULT '[]'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_message_external_id ON messages(external_message_id) WHERE external_message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at DESC);

CREATE TABLE IF NOT EXISTS courses (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), code text NOT NULL UNIQUE, title text NOT NULL,
 description text NOT NULL DEFAULT '', fee_amount numeric(12,2), fee_currency char(3) NOT NULL DEFAULT 'INR',
 fee_basis text, fee_verified boolean NOT NULL DEFAULT false, duration_weeks integer CHECK (duration_weeks IS NULL OR duration_weeks>0),
 schedule_text text, schedule_timezone text NOT NULL DEFAULT 'Asia/Kolkata', eligibility_text text,
 discount_policy_text text, placement_claim_text text, start_date date,
 status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','inactive','draft_demo_only')),
 approved_by uuid REFERENCES app_users(id) ON DELETE SET NULL, approved_at timestamptz,
 content_updated_at timestamptz NOT NULL DEFAULT now(), created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(), metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 CHECK (fee_amount IS NULL OR fee_amount>=0), CHECK (status<>'approved' OR approved_at IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_courses_status_title ON courses(status,title);

CREATE TABLE IF NOT EXISTS knowledge_documents (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), logical_key text NOT NULL, version integer NOT NULL CHECK (version>0),
 title text NOT NULL, document_type text NOT NULL CHECK (document_type IN ('course','fee_policy','schedule','eligibility','discount_policy','placement_policy','refund_policy','faq','other')),
 content text NOT NULL, status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','expired','rejected')),
 valid_from timestamptz, valid_until timestamptz, approved_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
 approved_at timestamptz, updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
 created_at timestamptz NOT NULL DEFAULT now(), content_hash text, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 UNIQUE(logical_key,version), CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until>valid_from),
 CHECK (status<>'approved' OR approved_at IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_kb_approved_valid ON knowledge_documents(status,valid_from,valid_until);

CREATE TABLE IF NOT EXISTS lead_objections (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 message_id uuid REFERENCES messages(id) ON DELETE SET NULL,
 objection_type text NOT NULL CHECK (objection_type IN ('fees','job_fears','family_approval','time','eligibility','location','trust','other')),
 evidence_text text, confidence numeric(4,3) CHECK (confidence IS NULL OR (confidence BETWEEN 0 AND 1)),
 status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','addressed','dismissed')),
 detected_by text NOT NULL DEFAULT 'ai' CHECK (detected_by IN ('ai','counselor','system')),
 created_at timestamptz NOT NULL DEFAULT now(), resolved_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_objections_lead_status ON lead_objections(lead_id,status,created_at DESC);

CREATE TABLE IF NOT EXISTS aptitude_questions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), question_key text NOT NULL, version integer NOT NULL DEFAULT 1,
 question_text jsonb NOT NULL, options jsonb NOT NULL, scoring_rubric jsonb NOT NULL,
 skill_dimension text NOT NULL, is_active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(question_key,version)
);
CREATE TABLE IF NOT EXISTS aptitude_assessments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 status text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress','completed','abandoned')),
 language text NOT NULL DEFAULT 'en', goal_summary text, score numeric(5,2) CHECK (score IS NULL OR score BETWEEN 0 AND 100),
 result_summary text, recommended_course_ids jsonb NOT NULL DEFAULT '[]'::jsonb, recommendation_rationale text,
 started_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz,
 created_by text NOT NULL DEFAULT 'ai' CHECK (created_by IN ('ai','counselor'))
);
CREATE INDEX IF NOT EXISTS idx_assessments_lead_started ON aptitude_assessments(lead_id,started_at DESC);

CREATE TABLE IF NOT EXISTS aptitude_responses (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), assessment_id uuid NOT NULL REFERENCES aptitude_assessments(id) ON DELETE CASCADE,
 question_id uuid NOT NULL REFERENCES aptitude_questions(id) ON DELETE RESTRICT, answer_text text, selected_option_key text,
 score_awarded numeric(6,2) NOT NULL DEFAULT 0, max_score numeric(6,2) NOT NULL DEFAULT 0,
 response_order integer NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(assessment_id,question_id), UNIQUE(assessment_id,response_order)
);

CREATE TABLE IF NOT EXISTS demo_slots (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), course_id uuid REFERENCES courses(id) ON DELETE SET NULL,
 starts_at timestamptz NOT NULL, ends_at timestamptz NOT NULL, timezone text NOT NULL DEFAULT 'Asia/Kolkata',
 capacity integer NOT NULL DEFAULT 1 CHECK (capacity>0),
 status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed','cancelled')),
 provider text NOT NULL DEFAULT 'mock', provider_event_id text,
 provider_mode text NOT NULL DEFAULT 'simulated' CHECK (provider_mode IN ('real','simulated')),
 created_at timestamptz NOT NULL DEFAULT now(), CHECK (ends_at>starts_at), UNIQUE(provider,provider_event_id)
);
CREATE INDEX IF NOT EXISTS idx_demo_slots_open_start ON demo_slots(status,starts_at) WHERE status='open';

CREATE TABLE IF NOT EXISTS demo_bookings (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 slot_id uuid NOT NULL REFERENCES demo_slots(id) ON DELETE RESTRICT,
 status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','cancelled','failed','attended','no_show')),
 provider_booking_id text, provider_mode text NOT NULL DEFAULT 'simulated' CHECK (provider_mode IN ('real','simulated')),
 booked_by_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
 confirmation_message_id uuid REFERENCES messages(id) ON DELETE SET NULL,
 reminder_scheduled_at timestamptz, reminder_sent_at timestamptz, cancelled_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(provider_mode,provider_booking_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_one_active_booking_per_lead_slot ON demo_bookings(lead_id,slot_id) WHERE status IN ('pending','confirmed');
CREATE INDEX IF NOT EXISTS idx_bookings_slot_status ON demo_bookings(slot_id,status);

CREATE TABLE IF NOT EXISTS follow_up_tasks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 conversation_id uuid REFERENCES conversations(id) ON DELETE SET NULL,
 assigned_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
 channel text CHECK (channel IN ('whatsapp','instagram','phone_call','email','manual','other')),
 action_type text NOT NULL CHECK (action_type IN ('reply_question','send_follow_up','call_lead','confirm_fee','confirm_policy','book_demo','remind_demo','human_counseling','review_identity','other')),
 reason text NOT NULL, suggested_message text, scheduled_at timestamptz,
 priority smallint NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
 status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','in_progress','completed','snoozed','cancelled','failed')),
 idempotency_key text UNIQUE, outcome text,
 created_by text NOT NULL DEFAULT 'system' CHECK (created_by IN ('system','ai','counselor')),
 created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_followups_due_status ON follow_up_tasks(status,scheduled_at,priority DESC);
CREATE INDEX IF NOT EXISTS idx_followups_lead ON follow_up_tasks(lead_id,created_at DESC);

CREATE TABLE IF NOT EXISTS lead_score_history (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 old_score smallint CHECK (old_score IS NULL OR old_score BETWEEN 0 AND 100),
 new_score smallint NOT NULL CHECK (new_score BETWEEN 0 AND 100),
 reasons jsonb NOT NULL DEFAULT '[]'::jsonb, model_or_rule_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_score_history_lead_time ON lead_score_history(lead_id,created_at DESC);

CREATE TABLE IF NOT EXISTS lead_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 event_type text NOT NULL, actor_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
 channel text, related_entity_type text, related_entity_id uuid,
 payload jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lead_events_timeline ON lead_events(lead_id,created_at DESC);

CREATE TABLE IF NOT EXISTS provider_webhook_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), provider text NOT NULL, provider_event_id text NOT NULL,
 event_type text NOT NULL, signature_valid boolean NOT NULL DEFAULT false,
 processing_status text NOT NULL DEFAULT 'received' CHECK (processing_status IN ('received','queued','processing','processed','failed','ignored')),
 payload jsonb NOT NULL, error_message text, received_at timestamptz NOT NULL DEFAULT now(), processed_at timestamptz,
 UNIQUE(provider,provider_event_id)
);
CREATE INDEX IF NOT EXISTS idx_webhook_processing ON provider_webhook_events(processing_status,received_at);

CREATE TABLE IF NOT EXISTS lead_source_touches (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
 source text NOT NULL, campaign text, landing_page text, external_click_id text,
 touched_at timestamptz NOT NULL DEFAULT now(), metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_source_touches_lead_time ON lead_source_touches(lead_id,touched_at);
