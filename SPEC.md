# AI Lead Desk — Product Specification

Status: Hackathon MVP v1.0. Default timezone: Asia/Kolkata. Single-institute admissions MVP.

## Problem and goal
Enquiries arrive via WhatsApp, phone, Instagram, website forms and walk-ins, including after-hours voice notes and English/Hindi/Marathi code-switching. AI Lead Desk unifies identities and timelines, supports transparent AI counselling, books demos into actual available slots, and prevents forgotten follow-ups.

## MVP scope (P0)
1. Unified lead inbox with search, stage/source/score filters, assignment and timeline.
2. Channel identity mapping and duplicate review. Exact verified phone/email/provider ID can match; names/transliteration are candidate signals only and must not trigger irreversible automatic merges.
3. Inbound/outbound/internal message history with channel, language, media/transcript, delivery state and provider IDs.
4. AI counselor discovers background, goals, availability and constraints; answers only from approved institute knowledge; responds in the prospect's language/register; escalates unknown facts.
5. Four sample courses in the included knowledge base, clearly marked fictional demo values.
6. Short adaptive aptitude check; persist question versions, answers, scoring rubric, result and recommendation rationale. This is not a validated psychometric test or admission decision.
7. Demo booking from provider-confirmed free slots, reminders, cancellation/rescheduling. Simulated calendar must be visibly labelled.
8. Next-best-action queue considers behavior, stage, objection, last contact, consent, preferred channel, quiet hours and outreach frequency.
9. Dashboard cards: lead score (0–100 heuristic, not admission probability), three-line summary, objections (fees, job fears, family approval, time, eligibility, location, trust, other), suggested next message, human takeover.
10. Analytics for enquiry-to-demo-to-admission grouped by first-touch source, counselor and objection.

P1 if time: WhatsApp Cloud API, Instagram DMs, speech-to-text for audio, Indian telephony provider, real calendar integration, outbound reminders and richer analytics. Do not claim an integration is live when mocked.

## Hard counselor rules
- Fees, discounts, durations, schedules, eligibility, refund rules and placement claims must be grounded in currently approved institute records. No model-memory guessing.
- If a requested fact is missing, expired, contradictory or unapproved: say it needs confirmation and create a counselor task.
- Never promise jobs, salary, admission or outcomes unless the institution has an approved and accurately worded policy; never turn support services into guarantees.
- Human takeover pauses AI outbound messages until the counselor releases the conversation.
- Respect consent, opt-outs, provider policies, rate limits and quiet hours. No unsolicited bulk messaging in MVP.
- Validate webhook signatures, deduplicate provider events, keep secrets out of source control/logs, and audit identity merges, knowledge approvals and exports.

## Suggested stack
Frontend: Next.js + TypeScript. API: Python + FastAPI under /api/v1. Database: PostgreSQL with UUIDs, JSONB metadata and UTC timestamps. Worker: Redis-backed queue/scheduler. AI: provider-agnostic LLM plus retrieval restricted to approved KB versions. Channel, speech and calendar integrations are adapters; mocks are explicitly labelled.

## Core relationships
Leads connect to identities, conversations, events, objections, follow-up tasks, score history and aptitude assessments. Conversations connect to messages. Courses connect to demo slots; bookings connect leads to slots. Versioned knowledge documents control what AI may answer. Provider webhook events are idempotent by provider/event ID. Full schema: database/schema.sql.

## Explainable score
Baseline 0–100: declared intent up to 30, responsiveness/recency up to 20, fit with stated prerequisites up to 20, demo interest/booked up to 15, concrete next step up to 15. Persist components and version. Do not infer protected characteristics or describe score as admission probability. Consent/opt-out overrides any score.

## Analytics definitions
Enquiry = canonical lead first created in selected cohort, attributed to first-touch source; preserve later touchpoints. Demo booked = confirmed booking. Demo attended = explicitly recorded attendance. Admission = authorized user sets stage to admitted and timestamp. Conversion = admitted eligible leads / eligible leads; return numerator, denominator, cohort dates and timezone. Objection conversion is correlation, not causation.

## Acceptance criteria
- Form lead followed by verified WhatsApp identity appears on one timeline.
- Name/transliteration similarity alone produces a candidate, not automatic merge.
- Inbox lists score, owner, summary, objections and next action.
- English, Hindi, Marathi and mixed messages receive matching-register responses.
- Unknown fee/discount/placement questions never get invented answers and create a task.
- Course facts have approval state; sample values are marked fictional.
- Aptitude result and rationale are stored and explainable.
- Booking is confirmed only after calendar success; mock slots show simulated.
- Follow-up respects opt-out, quiet hours, idempotency and handoff.
- Analytics filter by source, counselor and objection.
- Feature work uses branches and PRs into main.

## Contracts
Endpoint list and payloads: docs/API_SPEC.md. PostgreSQL tables/indexes: database/schema.sql. Read docs/DECISIONS.md and docs/TEAM_WORKFLOW.md before splitting work.
