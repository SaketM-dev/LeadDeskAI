# Aptitude interest assessment

## What is implemented

The workspace **Aptitude assessment** section now provides a structured 30-item career-interest inventory. It uses six interest areas inspired by the RIASEC framework: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. The live question bank is seeded by `database/migrations/20261017_career_counseling_30_questions.sql`; the demo mode includes the same 30-item flow. A counselor selects an existing lead, optionally records the learner's goal, and starts the assessment. In live mode, the API saves each response, prevents duplicate answers, finalizes a result, and stores ranked interest areas across six RIASEC-inspired dimensions and course discussion recommendations in PostgreSQL.

**Standardization note:** this is a structured career-interest inventory inspired by RIASEC, not a licensed, normed, or psychometrically validated standardized test. It must not be presented as one or used for admission/eligibility decisions. It is a preference exploration tool; the completion percentage measures answered questions, not ability. Recommendations are discussion starters for a trained counselor. The completion percentage measures answered questions; recommendations are conversation starters. No messages are sent automatically.

## Database setup

The connected Supabase project already has the schema and active aptitude questions. For a fresh project, follow the complete ordered migration list in `database/SUPABASE_SETUP.md`; do not run the baseline `database/schema.sql` against the connected project.

## Live-mode configuration

- Set `DATABASE_URL` on the backend to the intended PostgreSQL/Supabase connection.
- Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` on both frontend-server and backend environments.
- Provision the Supabase Auth account UUID in `public.app_users` with an active staff role.
- Set `NEXT_PUBLIC_DEMO_MODE=false` in `frontend/.env.local` and restart Next.js.
- Start/restart FastAPI and Next.js. Open Workspace → Aptitude assessment and select an existing live lead.

The assessment endpoints require a signed-in Supabase Auth staff session:
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
