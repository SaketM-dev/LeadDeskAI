-- Production compatibility migration for the existing AI Lead Desk schema.
-- Additive only: preserves existing leads/courses/activities and does not rename or drop columns.
-- Apply before 20261017_admissions_workflows.sql and then the aptitude/follow-up compatibility migrations.
BEGIN;

ALTER TABLE public.leads
  ADD COLUMN IF NOT EXISTS normalized_name text,
  ADD COLUMN IF NOT EXISTS preferred_language text DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS stage text,
  ADD COLUMN IF NOT EXISTS lead_score smallint NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS score_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS three_line_summary text,
  ADD COLUMN IF NOT EXISTS assigned_user_id uuid,
  ADD COLUMN IF NOT EXISTS first_touch_source text,
  ADD COLUMN IF NOT EXISTS last_touch_source text,
  ADD COLUMN IF NOT EXISTS marketing_consent boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS whatsapp_consent boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS email_consent boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS do_not_contact boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS last_inbound_at timestamptz,
  ADD COLUMN IF NOT EXISTS admitted_at timestamptz,
  ADD COLUMN IF NOT EXISTS merged_into_lead_id uuid;

-- Backfill new compatibility fields from the legacy columns without overwriting
-- any values that may already have been populated by an earlier deployment.
UPDATE public.leads
SET
  normalized_name = COALESCE(normalized_name, lower(regexp_replace(trim(full_name), '\\s+', ' ', 'g'))),
  preferred_language = COALESCE(NULLIF(preferred_language, ''), 'unknown'),
  stage = COALESCE(stage, CASE
    WHEN status IN ('new', 'contacted', 'qualified', 'demo_booked', 'demo_attended',
                    'nurturing', 'admitted', 'lost', 'do_not_contact') THEN status
    WHEN status IN ('converted', 'enrolled', 'closed_won') THEN 'admitted'
    WHEN status IN ('unqualified', 'closed_lost', 'rejected') THEN 'lost'
    ELSE 'new'
  END),
  assigned_user_id = COALESCE(assigned_user_id, assigned_to),
  first_touch_source = COALESCE(first_touch_source, source, 'manual'),
  last_touch_source = COALESCE(last_touch_source, source, 'manual')
WHERE normalized_name IS NULL
   OR preferred_language IS NULL OR preferred_language = ''
   OR stage IS NULL OR assigned_user_id IS NULL
   OR first_touch_source IS NULL OR last_touch_source IS NULL;

ALTER TABLE public.leads
  ALTER COLUMN stage SET DEFAULT 'new';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.leads'::regclass
      AND conname = 'leads_stage_compat_check'
  ) THEN
    ALTER TABLE public.leads
      ADD CONSTRAINT leads_stage_compat_check
      CHECK (stage IN ('new','contacted','qualified','demo_booked','demo_attended',
                       'nurturing','admitted','lost','do_not_contact')) NOT VALID;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_leads_compat_stage_updated
  ON public.leads(stage, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_compat_assignee_score
  ON public.leads(assigned_user_id, lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_compat_source_created
  ON public.leads(first_touch_source, created_at DESC);

COMMIT;

-- Verification (run separately after migration):
-- SELECT count(*) AS leads_missing_stage FROM public.leads WHERE stage IS NULL;
-- SELECT stage, count(*) FROM public.leads GROUP BY stage ORDER BY stage;
