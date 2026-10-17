# AI Lead Desk

AI-assisted admissions lead management for education teams. The application is designed to unify enquiries, counselor conversations, approved course knowledge, aptitude guidance, demo bookings, follow-up tasks, and admissions analytics.

> **Demo data warning:** Sample course fees, durations, and schedules in `knowledge_base/courses.json` are fictional placeholders, not verified details about TechSummitTrainers or any institute. They must be reviewed and approved before prospect-facing use.

## Shared project contracts

- `SPEC.md` — product scope, workflow, architecture, and acceptance criteria.
- `docs/API_SPEC.md` — API endpoints and payload contracts.
- `database/schema.sql` — existing PostgreSQL schema.
- `database/migrations/20261017_admissions_workflows.sql` — additive tables proposed for sessions, conversations, assessments, tasks, bookings, knowledge versions and audit events. **Not yet applied to a live database.**
- `knowledge_base/KNOWLEDGE_BASE.md` and `knowledge_base/courses.json` — counselor rules and sample knowledge.
- `docs/DECISIONS.md`, `docs/TEAM_WORKFLOW.md`, and `docs/FRONTEND.md` — shared architecture, collaboration and frontend guidance.

## Architecture

- Frontend: Next.js App Router and TypeScript (`frontend/`).
- Business API: Python FastAPI; target contract under `/api/v1`.
- Database: PostgreSQL.
- Jobs and reminders: worker-backed jobs where implemented.
- External channels, AI and calendar providers: adapter-based; disconnected providers must be labelled as simulated.

## Frontend dark theme

The workspace now has a dark token foundation in `frontend/app/globals.css`, semantic Tailwind tokens in `frontend/tailwind.config.ts`, a dark responsive app shell, a dark sign-in screen, and reusable UI primitives in `frontend/components/ui.tsx`. Existing feature screens are being migrated incrementally; the compatibility CSS remaps many legacy light palette utilities to the dark tokens.

## Run the backend

The current FastAPI backend implements health checks, a database connectivity check, the lead-list read endpoint, and a voice-provider status endpoint. The rest of the product API in `docs/API_SPEC.md` remains a target contract unless explicitly implemented and tested.

1. Create a local virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`. Set `GROQ_API_KEY` to a valid Groq key for hosted chatbot inference. Keep all real secrets in `.env` or deployment secrets; never commit them. If `DATABASE_URL` is omitted, the API starts with a local SQLite demo file so health checks and the chatbot can run, but database-backed lead features require your PostgreSQL/Supabase URL and the schema.
3. Apply `database/schema.sql` only after checking that the target database is correct and backed up. The additive workflow migration must also be reviewed and intentionally applied before its tables can be used. Neither database change has been verified against your live Supabase instance in this task.
4. Start the API from the repository root:

   ```bash
   uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
   ```

5. Verify `http://127.0.0.1:8000/health`, `http://127.0.0.1:8000/health/database`, and `http://127.0.0.1:8000/docs`.

Backend smoke tests:

```bash
source .venv/bin/activate
PYTHONPATH=backend DATABASE_URL=sqlite:///./test.db pytest -q backend/tests
```

The SQLite URL above is for smoke tests only. The production lead query uses PostgreSQL-specific schema qualification and expects the schema to be applied.

## Configure the Groq chatbot

The floating multilingual chatbot uses Groq-hosted `openai/gpt-oss-20b` inference. The API key is a private runtime secret and **must not be committed to GitHub**.

1. In the repository root, create your private local environment file by copying `.env.example` to `.env`.
2. Add these values to `.env` (replace the placeholder with a newly created key from https://console.groq.com/keys):

   ```dotenv
   GROQ_API_KEY=your_new_groq_api_key
   GROQ_MODEL=openai/gpt-oss-20b
   ```

3. Restart the FastAPI process after editing `.env`. The backend loads this file itself; do not put the key in frontend variables, source code, or a committed file.
4. Send a test request in English, Hindi, or Marathi through the floating chat widget. A valid key and available provider quota are required for a real response.

If the key was exposed in chat, screenshots, or Git history, revoke it and create a replacement. The repository's `.gitignore` excludes `.env` files.

## Run the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Validation

```bash
npm run type-check
npm run lint
npm run build
```

The default configuration enables demo mode so the frontend can be explored without a running backend. Set `NEXT_PUBLIC_DEMO_MODE=false` only when the API is configured. Live API failures must remain visible; the UI must not silently substitute mock data.

## Current implementation limits

- Authentication, password reset, server sessions and role-enforced route/API authorization are not implemented by the existing backend. The sign-in page is a non-authenticating UI.
- Live lead listing is implemented outside the planned `/api/v1` contract. Lead create/update, conversations, aptitude persistence, course CRUD, demo-slot booking, follow-up CRUD, analytics, knowledge management and user administration are not end-to-end backend features yet.
- External providers must be explicitly connected and verified before showing a Connected status. Otherwise label them **Simulated**.
- The additive migration is a proposed database change, not proof of a working database connection.

## Safety rules

- Never invent course fees, schedules, discounts, eligibility, or placement guarantees.
- Use approved, current knowledge for course-specific claims.
- Unsupported questions should be escalated for counselor confirmation.
- Never merge leads solely because their names look similar.
- Confirm bookings only after backend/provider confirmation.
- Respect consent, opt-outs, quiet hours, and human takeover.
- Never commit secrets or real prospect personal data.

Do not describe the application as production-ready until the missing routes, auth controls, live database connection, provider integrations and end-to-end tests are implemented and verified.


## Synthetic chat data and XGBoost lead scoring

The repository includes `data/synthetic_chat_enquiries.csv` with 120 fictional enquiry conversations in English, Hindi, and Marathi. Every row is synthetic and the `converted` field is a simulated label generated from transparent intent patterns; it is not actual student/admissions outcome data.

### Train and evaluate the demo model

Install root dependencies, then run:

```bash
python scripts/train_lead_scoring.py
```

This trains an XGBoost binary classifier and writes `artifacts/lead_intent_xgboost.json` plus a metrics report. The API lazily trains an in-memory model from the bundled synthetic CSV if you haven't run the script first.

### API endpoints

- `GET /api/lead-scoring/training-data` — aggregate count of synthetic examples and labels.
- `POST /api/lead-scoring/score` — request body such as `{"transcript":"I want to book a demo next week","language":"en"}`.

The returned score is an experimental enquiry-priority estimate only. Synthetic-only metrics do not establish real-world accuracy. Do not use it to reject applicants, decide eligibility, or make other high-impact decisions. Replace the synthetic data and validate the model on consented, representative, historical outcomes before any operational use.


## Follow-up UI/backend integration

The Follow-ups workspace can read and mutate real task records when live mode is enabled. The frontend calls the existing token-protected `/api/v1/follow-ups` endpoints for list, create, reschedule, and completion. In demo mode, seeded tasks are explicitly local-only and are never represented as saved backend records.

To use live follow-ups, configure `DATABASE_URL`, `LEAD_DESK_API_TOKEN`, and apply the admissions workflow schema/migration to the database. Set `NEXT_PUBLIC_DEMO_MODE=false` in `frontend/.env.local` and restart Next.js. The API token must be supplied through the authenticated workspace setup; never commit it or expose it in a `NEXT_PUBLIC_*` variable. The database must contain a real lead before a follow-up can be created. Calendar bookings and outbound reminders remain separate integrations and are not implied by a saved follow-up.
