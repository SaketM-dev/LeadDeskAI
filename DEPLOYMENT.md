# Fast deployment guide

Repository: https://github.com/SaketM-dev/LeadDeskAI

## 1. Deploy the backend on Render

1. Create a Blueprint from this GitHub repository and select the `main` branch. Render reads `render.yaml` and creates `ai-lead-desk-api`.
2. Set `DATABASE_URL` to the Supabase PostgreSQL connection string and `SUPABASE_ANON_KEY` to the project's publishable/anon key in Render's private environment settings. `SUPABASE_URL` is already set in `render.yaml`.
3. Add `GROQ_API_KEY` only if hosted chatbot inference is needed.
4. Deploy, then check `https://YOUR-API.onrender.com/health`.

## 2. Deploy the frontend on Vercel

1. Import the same GitHub repository and set **Root Directory** to `frontend`.
2. Use Next.js, `npm install`, and `npm run build`.
3. Set server environment variables `BACKEND_API_URL`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY`. Do not prefix these with `NEXT_PUBLIC_`.
4. Keep `NEXT_PUBLIC_DEMO_MODE=true` while setting up authentication and verifying the live database.
5. Set `NEXT_PUBLIC_DEFAULT_TIMEZONE=Asia/Kolkata` and deploy.

## 3. Finish Supabase setup

Apply the migration order in [database/SUPABASE_SETUP.md](database/SUPABASE_SETUP.md), including the Supabase Auth staff mapping migration. In Supabase Authentication, create staff accounts, then insert their Auth UUIDs into `public.app_users` with their assigned roles. Use only `administrator`, `admissions_manager`, or `admissions_counselor`; staff must be active to enter the workspace.

Set the Supabase Auth Site URL to the Vercel domain and allow that domain in redirect URLs. The login page signs in through Supabase Auth. The backend checks each token and the matching active staff role. Lead assignment and knowledge-base approval are restricted to managers and administrators.

## 4. Enable live mode

After both services have the required environment variables and the database is reachable, sign in as a provisioned staff user and confirm an unprovisioned account is denied. Then change `NEXT_PUBLIC_DEMO_MODE=false` in Vercel and redeploy. The browser never receives the database URL or Supabase access token; the frontend server proxies API calls using an HttpOnly session cookie.

## Known limitations

Several screens are illustrative, and WhatsApp/Instagram/telephony and real calendar integrations require separate provider setup. Review `README.md` for endpoint limitations and the experimental nature of lead scoring. Render's free service can sleep when idle.
