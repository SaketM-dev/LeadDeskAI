# Fast deployment guide

Repository: https://github.com/SaketM-dev/LeadDeskAI

## 1. Deploy the frontend on Vercel

1. Sign in at https://vercel.com/new and import `SaketM-dev/LeadDeskAI`.
2. Set **Root Directory** to `frontend`.
3. Framework preset: **Next.js**. Build command: `npm run build`. Install command: `npm install`.
4. Add environment variables:
   - `NEXT_PUBLIC_DEMO_MODE` = `true` (fastest demo; uses local seeded demo data)
   - `NEXT_PUBLIC_DEFAULT_TIMEZONE` = `Asia/Kolkata`
   - `BACKEND_API_URL` = the public Render API URL after Step 2. Initially it can be omitted only if the build succeeds without it; live backend calls will not work until set.
5. Click **Deploy**. Copy the resulting Vercel URL.

Important: the frontend is currently configured for demo mode by default. Demo data is browser/local demo data, not shared persistent data across visitors.

## 2. Deploy the backend on Render

1. Sign in at https://dashboard.render.com/ and choose **New + → Blueprint**.
2. Connect the same GitHub repository and select branch `main`.
3. Render reads `render.yaml` and creates the `ai-lead-desk-api` web service.
4. Once deployed, open `https://YOUR-API.onrender.com/health`; expect JSON with status healthy. Also check `/docs`.
5. In Render environment settings, add `GROQ_API_KEY` if real chatbot inference is needed. Never put this key in Vercel's `NEXT_PUBLIC_*` variables or GitHub.
6. Copy the Render URL.

Render's free services can sleep when idle and may take time to wake up.

## 3. Connect Vercel to Render

1. In Vercel → Project → Settings → Environment Variables, set `BACKEND_API_URL` to the exact Render base URL (no trailing slash), e.g. `https://ai-lead-desk-api.onrender.com`.
2. Keep `NEXT_PUBLIC_DEMO_MODE=true` for the fastest safe demo. Redeploy the Vercel project after changing environment variables.
3. Verify the public Vercel site loads and the API health URL works.

## 4. Supabase / live database (only if needed)

The backend's database-backed features require a valid `DATABASE_URL` and the repository's schema/migrations to be reviewed and applied to the intended Supabase project. Do not apply SQL blindly. Add `DATABASE_URL` only in Render's private environment settings. Use the Supabase PostgreSQL connection string, preferably the connection option recommended for your deployment network. Do not expose it to the browser.

Do not set `NEXT_PUBLIC_DEMO_MODE=false` until the backend database and required tables have been verified. Otherwise database-backed screens can fail. The sign-in page is currently UI-only, not production authentication.

## 5. Basic checks

- Frontend: open the Vercel URL in a private/incognito window.
- Backend: `/health` and `/docs` return successfully.
- Demo mode: verify seeded leads and the demo chat widget appear.
- Live mode: only test after configuring Supabase, applying reviewed schema/migrations, and configuring any required API token/provider secrets.

## Known limitations

This setup deploys the existing repository; it does not make every planned workflow production-ready. Review `README.md` for features that are not yet end-to-end, authentication limitations, and the experimental nature of synthetic-data lead scoring.
