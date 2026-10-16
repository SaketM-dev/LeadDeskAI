# Frontend ↔ current FastAPI backend connection

This guide describes the backend that is currently present in `backend/app/main.py`, not every endpoint in the broader API specification.

## Current implemented routes

- `GET /health` — API process health.
- `GET /health/database` — checks the configured PostgreSQL connection.
- `GET /api/leads` — reads up to 100 unmerged leads and returns `{ "count": number, "leads": [...] }`.
- `GET /api/voice/status` — reports whether a voice provider is configured; it does not transcribe or translate audio.

The frontend's Next.js rewrite keeps the backend URL server-side:

- Browser request `/backend-api/leads` → FastAPI `/api/leads`.
- Browser request `/backend-api/health` → FastAPI `/health`.
- Browser request `/backend-api/health/database` → FastAPI `/health/database`.
- Browser request `/backend-api/voice/status` → FastAPI `/api/voice/status`.

FastAPI errors can use the standard `{ "detail": "..." }` shape. The frontend API client now displays that detail instead of hiding it behind a generic HTTP error.

## Local setup

1. Start PostgreSQL and verify the database credentials used in the repository-root `.env`.
2. Start the API from the repository root:

   ```bash
   source .venv/bin/activate
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. In `frontend/.env.local`, set:

   ```dotenv
   BACKEND_API_URL=http://127.0.0.1:8000
   NEXT_PUBLIC_API_BASE_URL=/backend-api
   NEXT_PUBLIC_DEMO_MODE=false
   NEXT_PUBLIC_DEFAULT_TIMEZONE=Asia/Kolkata
   ```

4. Restart Next.js after changing environment variables:

   ```bash
   cd frontend
   npm run dev
   ```

5. Verify in a browser:
   - `http://127.0.0.1:8000/health`
   - `http://127.0.0.1:8000/health/database`
   - `http://localhost:3000/backend-api/health`
   - `http://localhost:3000/backend-api/health/database`
   - `http://localhost:3000/backend-api/leads`

Do not put database credentials in `NEXT_PUBLIC_*` variables. Keep real `.env` and `.env.local` files out of Git.

## Known limitations

The current backend is not yet the full API described in `docs/API_SPEC.md`. At present, the frontend can read the live lead list and show a lead profile assembled from that list. Lead creation, stage updates, notes, human handoff/release, follow-up tasks, conversations, courses, bookings, and analytics are not implemented by the inspected backend routes; the frontend must not pretend those operations succeeded. Demo mode keeps its data local.

The database health route returns HTTP 503 when the database cannot be reached. Check the actual `DATABASE_URL`, PostgreSQL service, role/database existence, and whether `database/schema.sql` has been applied before treating live data as ready. Applying schema SQL is a deliberate database operation; this frontend does not migrate or modify the database automatically.

## Validation status

These instructions and route mappings are based on the repository code. A successful local end-to-end run, database connection, and production build must be verified in the developer environment; this commit does not claim those checks passed.


## Automated checks

GitHub Actions runs frontend type-checking, linting and a production build, plus backend Python compilation and API smoke tests. The backend tests use a local SQLite URL only to import the app and exercise endpoints that do not need schema data; they do not validate the actual PostgreSQL schema or a Supabase connection. Check the latest run before merging.
