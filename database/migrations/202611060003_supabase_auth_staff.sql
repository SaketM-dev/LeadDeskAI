-- Supabase Auth backed staff identities for the application API.
-- Passwords remain owned by Supabase Auth; app_users stores staff roles only.
BEGIN;

ALTER TABLE public.app_users
  ADD COLUMN IF NOT EXISTS supabase_auth_user_id uuid;

CREATE UNIQUE INDEX IF NOT EXISTS app_users_supabase_auth_user_id_uidx
  ON public.app_users (supabase_auth_user_id)
  WHERE supabase_auth_user_id IS NOT NULL;

ALTER TABLE public.app_users
  ALTER COLUMN password_hash DROP NOT NULL;

COMMENT ON COLUMN public.app_users.supabase_auth_user_id IS
  'UUID of the corresponding account in Supabase Auth; set only by an administrator.';
COMMENT ON COLUMN public.app_users.password_hash IS
  'Deprecated. Supabase Auth owns staff passwords; retained for compatibility.';

COMMIT;
