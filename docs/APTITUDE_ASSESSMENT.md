# Aptitude interest assessment

## What is implemented

The workspace **Aptitude assessment** section now provides a structured 30-item career-interest inventory. It uses six interest areas inspired by the RIASEC framework: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. The live question bank is seeded by `database/migrations/20261017_career_counseling_30_questions.sql`; the demo mode includes the same 30-item flow. A counselor selects an existing lead, optionally records the learner's goal, and starts the assessment. In live mode, the API saves each response, prevents duplicate answers, finalizes a result, and stores ranked interest areas across six RIASEC-inspired dimensions and course discussion recommendations in PostgreSQL.

**Standardization note:** this is a structured career-interest inventory inspired by RIASEC, not a licensed, normed, or psychometrically validated standardized test. It must not be presented as one or used for admission/eligibility decisions. It is a preference exploration tool; the completion percentage measures answered questions, not ability. Recommendations are discussion starters for a trained counselor. The completion percentage measures answered questions; recommendations are conversation starters. No messages are sent automatically.

## Database setup

1. Back up and verify the target Supabase/PostgreSQL project.
2. Apply `database/schema.sql` if the base aptitude tables are not already present. Review it first; do not blindly rerun a schema against a production database.
3. Apply `database/migrations/20261017_aptitude_assessment.sql` in the Supabase SQL editor or your normal migration workflow. It adds an `updated_at` column and seeds the original eight versioned questions using `ON CONFLICT DO NOTHING`. Then apply `database/migrations/20261017_career_counseling_30_questions.sql`: it deactivates the original eight questions and seeds 30 active career-interest questions. It does not delete assessment data. Apply migrations in order.
4. Verify the migration completed and that `public.aptitude_questions` has active questions.

The migration has been committed but has **not** been applied to your live Supabase project by this change.

## Live-mode configuration

- Set `DATABASE_URL` on the backend to the intended PostgreSQL/Supabase connection.
- Set `LEAD_DESK_API_TOKEN` on the backend.
- In AI Lead Desk → Workspace → Settings & access, save the same bearer token for this browser session.
- Set `NEXT_PUBLIC_DEMO_MODE=false` in `frontend/.env.local` and restart Next.js.
- Start/restart FastAPI and Next.js. Open Workspace → Aptitude assessment and select an existing live lead.

The assessment endpoints require `Authorization: Bearer <LEAD_DESK_API_TOKEN>`:
- `POST /api/v1/aptitude/assessments` — start an assessment.
- `GET /api/v1/aptitude/assessments/{id}/next-question` — retrieve the next unanswered active question.
- `POST /api/v1/aptitude/assessments/{id}/responses` — persist an answer.
- `POST /api/v1/aptitude/assessments/{id}/complete` — finalize and persist the result.

The frontend's demo mode uses illustrative sample leads and does not persist responses. It is explicitly labelled **DEMO · LOCAL ONLY**. Live mode is labelled **LIVE · PERSISTED** and requires a real UUID lead returned from the API.

## Validation

From the repository root:

```bash
source .venv/bin/activate
PYTHONPATH=backend DATABASE_URL=sqlite:///./test.db pytest -q backend/tests
```

The aptitude tables and JSONB queries require PostgreSQL for end-to-end assessment persistence. The SQLite command is a smoke-test baseline and is not proof that the PostgreSQL workflow or deployed Supabase migration works. Also run from `frontend/`:

```bash
npm run type-check
npm run lint
npm run build
```

## Scoring and privacy

Each response records the selected option and an explicit rubric point in `aptitude_responses`. The final profile ranks interest dimensions by selected-option counts and maps them to course discussion topics. The overall percentage is completion/response coverage, not ability or conversion probability. The API does not send external messages and does not change a lead's admission status.
