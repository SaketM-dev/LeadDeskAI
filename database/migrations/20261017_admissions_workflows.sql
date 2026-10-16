-- Additive migration for the admissions workflow expansion.
-- Existing tables are not renamed or dropped. Review against the deployed
-- database before applying; this migration has not been run against Supabase.
BEGIN;

CREATE TABLE IF NOT EXISTS public.app_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  display_name text NOT NULL,
  role text NOT NULL CHECK (role IN ('admissions_counselor','admissions_manager','administrator')),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.app_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
  token_hash text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS app_sessions_user_expiry_idx ON public.app_sessions(user_id, expires_at);

CREATE TABLE IF NOT EXISTS public.conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  channel text NOT NULL CHECK (channel IN ('whatsapp','instagram','website','phone','email')),
  provider_mode text NOT NULL DEFAULT 'simulated' CHECK (provider_mode IN ('connected','simulated')),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
  human_takeover boolean NOT NULL DEFAULT false,
  preferred_language text NOT NULL DEFAULT 'en' CHECK (preferred_language IN ('en','hi','mr')),
  consent_checked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversations_lead_updated_idx ON public.conversations(lead_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.conversation_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  sender_type text NOT NULL CHECK (sender_type IN ('prospect','counselor','assistant','system')),
  body text NOT NULL CHECK (length(body) <= 10000),
  language text CHECK (language IN ('en','hi','mr')),
  provider_message_id text,
  simulated boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversation_messages_timeline_idx ON public.conversation_messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS public.aptitude_assessments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid REFERENCES public.leads(id) ON DELETE SET NULL,
  answers jsonb NOT NULL DEFAULT '{}'::jsonb,
  current_question integer NOT NULL DEFAULT 0 CHECK (current_question BETWEEN 0 AND 10),
  status text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress','completed')),
  result jsonb,
  created_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.follow_up_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  assigned_to uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  title text NOT NULL,
  suggested_message text,
  priority text NOT NULL DEFAULT 'medium' CHECK (priority IN ('low','medium','high')),
  due_at timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','completed','cancelled')),
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS follow_up_tasks_due_idx ON public.follow_up_tasks(status, due_at);

CREATE TABLE IF NOT EXISTS public.demo_bookings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','cancelled','rescheduled')),
  provider_mode text NOT NULL DEFAULT 'simulated' CHECK (provider_mode IN ('connected','simulated')),
  provider_event_id text,
  created_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (ends_at > starts_at),
  CHECK (status <> 'confirmed' OR provider_mode = 'connected')
);
CREATE INDEX IF NOT EXISTS demo_bookings_starts_idx ON public.demo_bookings(starts_at, status);

CREATE TABLE IF NOT EXISTS public.knowledge_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind text NOT NULL CHECK (kind IN ('course','faq','policy')),
  title text NOT NULL,
  body text NOT NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','archived')),
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  created_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS knowledge_articles_approved_idx ON public.knowledge_articles(status, kind);

CREATE TABLE IF NOT EXISTS public.knowledge_article_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id uuid NOT NULL REFERENCES public.knowledge_articles(id) ON DELETE CASCADE,
  version integer NOT NULL,
  title text NOT NULL,
  body text NOT NULL,
  status text NOT NULL CHECK (status IN ('draft','approved','archived')),
  changed_by uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  changed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(article_id, version)
);

CREATE TABLE IF NOT EXISTS public.audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid REFERENCES public.app_users(id) ON DELETE SET NULL,
  event_type text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_events_entity_idx ON public.audit_events(entity_type, entity_id, created_at DESC);

COMMIT;
