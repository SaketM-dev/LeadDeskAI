-- Compatibility layer after the base/admissions schema migrations. Supports
-- fresh and existing Supabase projects; aligns active API queries without
-- deleting lead or course data.
BEGIN;

-- The base schema uses channel names from the original model, while the
-- inbound adapter stores the normalized channel names below.
DO $$
DECLARE constraint_row record;
BEGIN
  FOR constraint_row IN
    SELECT conname
    FROM pg_constraint
    WHERE conrelid = 'public.conversations'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) ILIKE '%channel%'
  LOOP
    EXECUTE format('ALTER TABLE public.conversations DROP CONSTRAINT %I', constraint_row.conname);
  END LOOP;
END $$;

ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS provider_mode text NOT NULL DEFAULT 'simulated',
  ADD COLUMN IF NOT EXISTS human_takeover boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS preferred_language text NOT NULL DEFAULT 'en',
  ADD COLUMN IF NOT EXISTS consent_checked_at timestamptz;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.conversations'::regclass
      AND conname = 'conversations_channel_fresh_check'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_channel_fresh_check
      CHECK (channel IN ('whatsapp','instagram','website','phone','email','phone_call','website_form','walk_in','manual','other'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.conversations'::regclass
      AND conname = 'conversations_provider_mode_fresh_check'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_provider_mode_fresh_check
      CHECK (provider_mode IN ('connected','simulated'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.conversations'::regclass
      AND conname = 'conversations_preferred_language_fresh_check'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_preferred_language_fresh_check
      CHECK (preferred_language IN ('en','hi','mr'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS conversations_lead_updated_fresh_idx
  ON public.conversations(lead_id, updated_at DESC);

-- The current API records a pending simulated booking as a time range. The
-- original schema modeled bookings only through pre-created demo_slots.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'demo_bookings'
      AND column_name = 'slot_id'
  ) THEN
    ALTER TABLE public.demo_bookings ALTER COLUMN slot_id DROP NOT NULL;
  END IF;
END $$;

ALTER TABLE public.demo_bookings
  ADD COLUMN IF NOT EXISTS starts_at timestamptz,
  ADD COLUMN IF NOT EXISTS ends_at timestamptz,
  ADD COLUMN IF NOT EXISTS provider_event_id text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.demo_bookings'::regclass
      AND conname = 'demo_bookings_time_range_fresh_check'
  ) THEN
    ALTER TABLE public.demo_bookings
      ADD CONSTRAINT demo_bookings_time_range_fresh_check
      CHECK (starts_at IS NULL OR ends_at IS NULL OR ends_at > starts_at);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS demo_bookings_starts_status_fresh_idx
  ON public.demo_bookings(starts_at, status);

-- Supabase REST roles receive no row access by default: the backend must use
-- a private server-side PostgreSQL connection. Do not add anon/authenticated
-- policies until proper per-user authentication and authorization exist.
DO $$
DECLARE table_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'app_users','app_sessions','leads','lead_activities','lead_identities','conversations',
    'conversation_messages','messages','courses','knowledge_documents',
    'knowledge_articles','knowledge_article_versions','lead_notes','lead_events',
    'audit_events','aptitude_questions','aptitude_assessments','aptitude_responses',
    'follow_up_tasks','demo_slots','demo_bookings','lead_score_history',
    'provider_webhook_events','lead_source_touches','lead_objections'
  ]
  LOOP
    IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
      EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon, authenticated', table_name);
    END IF;
  END LOOP;
END $$;

COMMIT;
