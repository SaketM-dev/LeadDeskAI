# Team workflow

## Branch ownership
- feat/api-database: FastAPI routes, models/migrations, schema and tests.
- feat/ai-counselor: grounded retrieval, language handling, aptitude and objection extraction.
- feat/dashboard: lead inbox/detail, score/summary/objections, handoff and analytics UI.
- feat/integrations: inbound webhooks, speech transcription, calendar, reminders and mock adapters.

Create one unique branch per actual teammate. Combine workstreams if the team is smaller; assign additional branches if larger. Do not share a feature branch between multiple people.

## Commands
git clone https://github.com/SaketM-dev/LeadDeskAI.git
cd LeadDeskAI
git switch main
git pull --ff-only origin main
git switch -c feat/<your-workstream>
# edit and test
git add <files>
git commit -m "feat: describe the change"
git push -u origin feat/<your-workstream>

Open a pull request targeting main. Avoid feature commits directly to main.

## Definition of done
- API payloads match docs/API_SPEC.md or the spec is updated in same PR.
- Schema/migration changes and tests are included.
- Test duplicate webhook/provider failures, opt-out and human handoff paths.
- No secrets or real prospect PII are committed.
- Mock integrations are visibly labelled simulated.
- PR includes changed files, test results, limitations, and UI screenshots where useful.

## 24-hour integration order
1. Agree schema, endpoints and JSON contracts together.
2. Backend provides migrations, seeded DB and example responses.
3. Frontend builds against fixtures while AI integration proceeds.
4. AI returns structured output with approved KB source IDs and unsupported-question handling.
5. Integrations team completes one working end-to-end channel/calendar path; others may be labelled mocks.
6. Demo: form lead -> grounded counselor response -> aptitude -> booking -> follow-up -> analytics.
