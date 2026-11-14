# Supabase setup for the connected AI LEAD project

These migrations have been applied to the connected project. It already had legacy `public.leads`, `public.courses`, and `public.lead_activities` tables. It currently has 0 leads, 4 courses, and 0 lead activities. Preserve these rows while upgrading the schema.

Run these files in order in Supabase SQL Editor:

1. `migrations/20261018_production_schema_compat.sql`
2. `migrations/20261017_admissions_workflows.sql`
3. `migrations/202611060002_existing_project_extensions.sql`
4. `migrations/20261017_aptitude_assessment.sql`
5. `migrations/20261017_career_counseling_30_questions.sql`
6. `migrations/20261017_followup_schema_compat.sql`
7. `migrations/20261017_inbound_message_to_lead.sql`
8. `migrations/202611060001_fresh_supabase_compat.sql`
9. `migrations/202611060003_supabase_auth_staff.sql`

Do **not** run `schema.sql` on this connected project: its legacy `leads`, `courses`, and `conversations` tables do not match that baseline. The existing project compatibility migration preserves the old course columns, copies the old course name/fee/schedule to the current API fields, and leaves courses unapproved with `fee_verified=false` until their facts are reviewed.

Migration 8 enabled row-level security and removed direct `anon`/`authenticated` table grants. It did not create or delete policies. Seven pre-existing policies remain on `courses`, `leads`, and `lead_activities`, but the REST roles currently have no table grants, so those policies do not expose the tables through Supabase's Data API. Review them before restoring any direct access.

The auth staff migration (step 9) has been applied. It adds a Supabase Auth user ID mapping to `app_users` and makes the legacy `password_hash` optional. Create each staff login in Supabase Authentication, then provision its staff role in SQL:

```sql
INSERT INTO public.app_users (email, display_name, role, supabase_auth_user_id)
VALUES ('staff@example.com', 'Staff Name', 'administrator', 'SUPABASE_AUTH_USER_UUID');
```

Allowed roles are `administrator`, `admissions_manager`, and `admissions_counselor`. Only an administrator should provision staff or change roles. Disable access with `is_active=false` or delete the staff mapping.

The API validates Supabase access tokens and requires an active staff mapping. Knowledge-base approvals and lead assignments require an administrator or admissions manager. The Next.js proxy keeps access tokens in an HttpOnly cookie. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in both frontend-server and backend environments; set `DATABASE_URL` only in the backend environment. Keep `NEXT_PUBLIC_DEMO_MODE=true` until secrets are configured, at least one staff account is provisioned, and a real sign-in has been verified.
