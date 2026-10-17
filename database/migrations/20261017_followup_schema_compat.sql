-- Normalize follow_up_tasks for the /api/v1/follow-ups API.
-- Apply after the base schema/admissions workflow migration. Existing rows are preserved.
BEGIN;

DO $$
BEGIN
  IF to_regclass('public.follow_up_tasks') IS NULL THEN
    RAISE EXCEPTION 'public.follow_up_tasks is missing; apply the admissions workflow migration first';
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='reason'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='title'
  ) THEN
    ALTER TABLE public.follow_up_tasks RENAME COLUMN reason TO title;
  END IF;
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='scheduled_at'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='due_at'
  ) THEN
    ALTER TABLE public.follow_up_tasks RENAME COLUMN scheduled_at TO due_at;
  END IF;
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='assigned_user_id'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='assigned_to'
  ) THEN
    ALTER TABLE public.follow_up_tasks RENAME COLUMN assigned_user_id TO assigned_to;
  END IF;
END $$;

DO $$
DECLARE constraint_row record;
BEGIN
  FOR constraint_row IN
    SELECT conname FROM pg_constraint
    WHERE conrelid='public.follow_up_tasks'::regclass
      AND contype='c'
      AND (pg_get_constraintdef(oid) ILIKE '%priority%' OR pg_get_constraintdef(oid) ILIKE '%status%')
  LOOP
    EXECUTE format('ALTER TABLE public.follow_up_tasks DROP CONSTRAINT %I', constraint_row.conname);
  END LOOP;
END $$;

ALTER TABLE public.follow_up_tasks
  ADD COLUMN IF NOT EXISTS title text,
  ADD COLUMN IF NOT EXISTS suggested_message text,
  ADD COLUMN IF NOT EXISTS priority text NOT NULL DEFAULT 'medium',
  ADD COLUMN IF NOT EXISTS due_at timestamptz,
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS completed_at timestamptz,
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks'
      AND column_name='priority' AND data_type <> 'text'
  ) THEN
    ALTER TABLE public.follow_up_tasks ALTER COLUMN priority DROP DEFAULT;
    ALTER TABLE public.follow_up_tasks
      ALTER COLUMN priority TYPE text
      USING CASE
        WHEN priority::text IN ('1','2') THEN 'low'
        WHEN priority::text = '3' THEN 'medium'
        WHEN priority::text IN ('4','5') THEN 'high'
        WHEN lower(priority::text) IN ('low','medium','high') THEN lower(priority::text)
        ELSE 'medium'
      END;
    ALTER TABLE public.follow_up_tasks ALTER COLUMN priority SET DEFAULT 'medium';
  ELSE
    UPDATE public.follow_up_tasks
    SET priority = CASE
      WHEN lower(priority) IN ('low','medium','high') THEN lower(priority)
      WHEN priority IN ('1','2') THEN 'low'
      WHEN priority = '3' THEN 'medium'
      WHEN priority IN ('4','5') THEN 'high'
      ELSE 'medium'
    END
    WHERE priority IS NULL OR lower(priority) NOT IN ('low','medium','high');
  END IF;
END $$;

UPDATE public.follow_up_tasks
SET status = CASE lower(status)
  WHEN 'in_progress' THEN 'pending'
  WHEN 'snoozed' THEN 'pending'
  WHEN 'failed' THEN 'cancelled'
  WHEN 'canceled' THEN 'cancelled'
  ELSE lower(status)
END
WHERE status IS NULL OR lower(status) NOT IN ('pending','completed','cancelled');

UPDATE public.follow_up_tasks
SET due_at = now() WHERE due_at IS NULL;
UPDATE public.follow_up_tasks
SET title = COALESCE(NULLIF(title, ''), 'Follow up')
WHERE title IS NULL OR title = '';
ALTER TABLE public.follow_up_tasks ALTER COLUMN title SET NOT NULL;
ALTER TABLE public.follow_up_tasks ALTER COLUMN due_at SET NOT NULL;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='follow_up_tasks' AND column_name='action_type'
  ) THEN
    ALTER TABLE public.follow_up_tasks ALTER COLUMN action_type SET DEFAULT 'other';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='public.follow_up_tasks'::regclass AND conname='follow_up_tasks_priority_check'
  ) THEN
    ALTER TABLE public.follow_up_tasks
      ADD CONSTRAINT follow_up_tasks_priority_check CHECK (priority IN ('low','medium','high'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='public.follow_up_tasks'::regclass AND conname='follow_up_tasks_status_check'
  ) THEN
    ALTER TABLE public.follow_up_tasks
      ADD CONSTRAINT follow_up_tasks_status_check CHECK (status IN ('pending','completed','cancelled'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS follow_up_tasks_due_idx ON public.follow_up_tasks(status, due_at);
COMMIT;
