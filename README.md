# AI Lead Desk

AI-assisted admissions lead management for education teams. The application is designed to unify enquiries, counselor conversations, approved course knowledge, aptitude guidance, demo bookings, follow-up tasks, and admissions analytics.

> **Demo data warning:** Sample course fees, durations, and schedules in `knowledge_base/courses.json` are fictional placeholders, not verified details about TechSummitTrainers or any institute. They must be reviewed and approved before prospect-facing use.

## Shared project contracts

- `SPEC.md` — product scope, workflow, architecture, and acceptance criteria.
- `docs/API_SPEC.md` — API endpoints and payload contracts.
- `database/schema.sql` — PostgreSQL schema.
- `knowledge_base/KNOWLEDGE_BASE.md` — counselor rules and sample knowledge.
- `knowledge_base/courses.json` — sample course records.
- `docs/DECISIONS.md` — shared architecture and data decisions.
- `docs/TEAM_WORKFLOW.md` — branch and integration workflow.
- `docs/FRONTEND.md` — frontend setup and architecture.

## Architecture

- Frontend: Next.js App Router and TypeScript (`frontend/`).
- Business API: Python FastAPI under `/api/v1`.
- Database: PostgreSQL.
- Jobs and reminders: worker-backed jobs where implemented.
- External channels, AI and calendar providers: adapter-based; disconnected providers must be labelled as simulated.

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

The default configuration enables demo mode so the frontend can be explored without a running backend. Set `NEXT_PUBLIC_DEMO_MODE=false` only when the API and required authentication are configured. The frontend must not silently fall back to mock data when live API requests fail.

## Safety rules

- Never invent course fees, schedules, discounts, eligibility, or placement guarantees.
- Use approved, current knowledge for course-specific claims.
- Unsupported questions should be escalated for counselor confirmation.
- Never merge leads solely because their names look similar.
- Confirm bookings only after backend/provider confirmation.
- Respect consent, opt-outs, quiet hours, and human takeover.
- Never commit secrets or real prospect personal data.

This repository includes the shared specification and frontend foundation. Backend routes and external integrations must be verified before being described as operational.
