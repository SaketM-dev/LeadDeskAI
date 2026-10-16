# AI Lead Desk — Frontend Foundation

## Stack
- Next.js App Router
- React and TypeScript
- Tailwind CSS
- Lucide icons
- Centralized API client
- Explicit demo mode

## Run locally

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Environment
`NEXT_PUBLIC_API_BASE_URL` is the FastAPI origin, for example `http://localhost:8000`. The API client appends `/api/v1`. `NEXT_PUBLIC_DEMO_MODE=true` uses clearly labelled demo fixtures. Live mode does not silently fall back to fixtures after an API failure.

## Architecture
- `app/`: Next.js routes and global styles.
- `lib/`: mode configuration, API client and shared utilities.
- `types/`: shared API types.
- `fixtures/`: fictional demo data only.
- `services/`: feature-level API operations as they are implemented.

## Safety
Sample course data in the root knowledge base is fictional and must not be presented as verified institute information. Keep credentials out of Git and never expose privileged Supabase keys in browser code. The documented business API is FastAPI under `/api/v1`; direct Supabase access must follow explicit team approval.

## Phase 1 scope
This is the technical foundation, not the complete dashboard or a claim that backend endpoints are already running. Feature pages and real integration are added in later stages.
