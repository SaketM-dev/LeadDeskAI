# API Specification — AI Lead Desk v1

Base path: /api/v1. JSON by default; multipart for audio. IDs are UUID strings. API timestamps are ISO-8601 UTC; display prospect-facing times in Asia/Kolkata unless a timezone is known.

## Conventions
List response: {"data":[...],"page":{"next_cursor":null}}.
Error: {"error":{"code":"VALIDATION_ERROR","message":"...","request_id":"...","details":[]}}.
Status codes: 200 read/update, 201 created, 202 asynchronous job accepted, 204 no body, 400 invalid request, 401 unauthenticated, 403 forbidden, 404 missing, 409 conflict/duplicate booking, 422 validation, 429 throttled, 502/503 provider unavailable.
Use Idempotency-Key for replies, bookings and side-effecting jobs. All write routes require auth and role/ownership checks.

## 1. Health and users
- GET /health — liveness.
- GET /ready — readiness probe; currently verifies database connectivity (worker status is not yet implemented).
- GET /api/v1/health — versioned liveness endpoint; does not require a database connection.
- GET /me — authenticated user and role.

## 2. Leads and timeline
- GET /leads — filters q, stage, source, assigned_to, min_score, objection, updated_after, limit, cursor.
- POST /leads — create manual/form lead. Body: full_name, optional phone/email, preferred_language, source, notes, consent.
- GET /leads/{lead_id} — lead profile and status.
- PATCH /leads/{lead_id} — update fields, stage, owner or consent; audit stage/owner changes.
- GET /leads/{lead_id}/timeline — ordered messages, events, identity changes, tasks, bookings and score history.
- POST /leads/{lead_id}/assign — {"user_id":"uuid"}; manager/admin only.
- POST /leads/{lead_id}/merge — {"duplicate_lead_id":"uuid","reason":"...","identity_evidence":[]} ; manager/admin, transactional, preserve history and audit.
- GET /leads/{lead_id}/identity-candidates — likely duplicates with evidence; name similarity alone must not auto-merge.
- POST /leads/{lead_id}/notes — counselor note.
- GET /leads/{lead_id}/next-action — suggested action and reasons.
- POST /leads/{lead_id}/handoff — reason human_requested|low_confidence|sensitive|other and optional assigned_user_id; pause AI.

Example create lead:
{"full_name":"Rahul Patil","phone":"+919876543210","email":"rahul@example.com","preferred_language":"mr","source":"website_form","consent":{"whatsapp":true,"marketing":false}}

## 3. Channel identities and conversations
- POST /leads/{lead_id}/identities — channel, provider_contact_id, phone_e164, email, display_name, verification_status.
- GET /leads/{lead_id}/conversations — list channel conversations.
- GET /conversations/{conversation_id} — metadata and takeover status.
- GET /conversations/{conversation_id}/messages — cursor-paginated history.
- POST /conversations/{conversation_id}/messages — counselor send: {"text":"...","language":"en","channel":"whatsapp"}; requires consent, permission, idempotency key.
- POST /conversations/{conversation_id}/takeover — assign human and suspend AI replies.
- POST /conversations/{conversation_id}/release-to-ai — resume only after explicit counselor release.
- POST /media/transcriptions — multipart upload; returns 202/job_id.
- GET /jobs/{job_id} — transcription/reminder state.

## 4. Counselor AI
- POST /counselor/respond — body: lead_id, conversation_id, inbound_message_id, text or transcript, detected_language, send_reply. Generates one grounded response; outbound send is separately permission/consent checked.
- POST /counselor/summarize/{lead_id} — update three-line summary, known facts, next action.
- POST /counselor/extract-objections/{message_id} — extract objection labels.

Example request:
{"lead_id":"uuid","conversation_id":"uuid","inbound_message_id":"uuid","text":"मला data analytics course ची fees आणि timing सांगा","detected_language":"mr","send_reply":false}

Response:
{"reply_text":"...","reply_language":"mr","intent":"course_fee_and_schedule","discovery_questions":[],"course_recommendations":[],"objections":[{"type":"fees","evidence_message_id":"uuid"}],"knowledge_sources":[{"document_id":"uuid","version":1,"fact_keys":["fee_amount","schedule_text"]}],"unsupported_questions":[],"human_handoff_required":false,"follow_up_task_id":null}

Hard rule: If approved current KB does not support a fact, never fill it from model memory. Tell the prospect confirmation is needed, populate unsupported_questions, and create a follow-up task. Never invent discounts or placement guarantees. Do not automatically send during human takeover, without consent, or when the channel is disconnected.

## 5. Courses and knowledge base
- GET /courses — active prospect-visible courses only.
- GET /courses/{course_id} — current course and freshness metadata.
- POST /courses — admin creates draft course.
- PATCH /courses/{course_id} — edit draft or submit changed version for review.
- POST /courses/{course_id}/approve — authorized approval of facts and validity period.
- GET /knowledge-base/documents — search approved records; admin can query drafts/expired.
- POST /knowledge-base/documents — create draft policy/FAQ/course document.
- PATCH /knowledge-base/documents/{document_id} — create new version; keep history.
- POST /knowledge-base/documents/{document_id}/approve — approve a version with validity.

Course facts: code, title, description, fee_amount/currency, fee_verified, duration_weeks, schedule_text/timezone, eligibility_text, discount_policy_text, placement_claim_text, status, content_updated_at, approved_by. AI retrieval may use only approved, current, unexpired records.

## 6. Aptitude and recommendations
- POST /aptitude/assessments — start for lead with goal and language.
- GET /aptitude/assessments/{assessment_id}/next-question — next adaptive question and options.
- POST /aptitude/assessments/{assessment_id}/responses — save answer and rubric score.
- POST /aptitude/assessments/{assessment_id}/complete — finalize score and explain recommendations/caveats.
- GET /leads/{lead_id}/recommendations — evidence and rationale.

## 7. Demo class calendar
- GET /demo-slots?course_id=&from=&to=&timezone=&available_only=true — provider-verified slots only.
- POST /demo-bookings — {"lead_id":"uuid","slot_id":"uuid","channel":"whatsapp"}; confirm only after calendar success.
- GET /demo-bookings/{booking_id} — state and provider status.
- POST /demo-bookings/{booking_id}/cancel — idempotently cancel event and booking.
- POST /demo-bookings/{booking_id}/reschedule — confirm new slot safely, then release old.
- POST /integrations/calendar/sync — admin sync/health trigger.

Booking state: pending, confirmed, cancelled, failed, attended, no_show. Mock provider must set provider_mode=simulated and UI must show a simulated label. Return 409 on booking conflict; don't rely on stale local availability.

## 8. Follow-up tasks
- GET /follow-ups — filters status, assignee, channel, due date and lead.
- POST /follow-ups — lead, channel, action_type, reason, suggested_message, scheduled_at, priority.
- PATCH /follow-ups/{task_id} — edit or snooze.
- POST /follow-ups/{task_id}/complete — close with outcome.
- POST /follow-ups/plan/{lead_id} — compute next action; planning does not itself send.
- POST /internal/jobs/follow-ups/run — worker-only: process due tasks while checking opt-out, quiet hours, deduplication and retry budget.

## 9. Dashboard and analytics
- GET /dashboard/summary — stage counts, overdue, new and unassigned leads.
- GET /analytics/conversions — date range and grouping by first-touch source, counselor or stage cohort.
- GET /analytics/objections — objection counts and stage-conversion summary.
- GET /analytics/sources — enquiries, demos, admissions and conversions by source.
- GET /analytics/counselors — assignments, follow-up SLA, demos and admissions.

Return numerator, denominator, cohort/date boundaries and timezone; do not report percentages alone. Correlation by objection is not causal evidence.

## 10. Webhooks and integration state
- POST /webhooks/whatsapp — verify signature, dedupe provider message/event ID, enqueue slow work.
- POST /webhooks/instagram — same pattern after permissions are configured.
- POST /webhooks/telephony/{provider} — call status/recording/transcript callback.
- POST /webhooks/calendar/{provider} — event changes if provider supports callbacks.
- GET /integrations/status — connected, mock, degraded or disconnected state.

## Required invariants
- lead_score is integer 0–100, not admission probability.
- provider webhooks, messages and booking side effects are idempotent.
- Opt-out blocks automated outbound messages on the relevant channel.
- Human takeover pauses AI replies until explicit release.
- Lead merge is transactional and preserves all identity and timeline history.
- Course-specific AI claims include source document/version IDs.


### Implemented subset (current branch)
- `GET /api/v1/health` — liveness probe.
- `GET /ready` — database readiness probe.
- `GET /api/v1/leads?q=&stage=&limit=` — listing protected by `Authorization: Bearer <LEAD_DESK_API_TOKEN>`. Fails closed with 503 when the token is not configured; supports bounded page size (1–100), optional name search and stage filter. Response includes `data` and `page.next_cursor` (currently null; cursor pagination is not implemented). Configure `LEAD_DESK_API_TOKEN` in the backend environment (see `.env.example`) before calling this route. Never place this secret in a `NEXT_PUBLIC_*` variable or commit a real value. This shared-token bootstrap is not a replacement for per-user sessions, role/ownership checks, or row-level security. `GET /api/v1/leads/{lead_id}` — returns one active lead by UUID, with 422 for invalid UUIDs and 404 when missing or merged. `POST /api/v1/leads` is also implemented as described below. `PATCH /api/v1/leads/{lead_id}` — updates supplied `full_name`, `preferred_language`, `stage`, consent flags, and `do_not_contact`; validates UUIDs and allowed values, rejects empty patches, and updates `updated_at`. Returns 404 for missing or merged records. `POST /api/v1/leads/{lead_id}/assign` is implemented: accepts `{\"user_id\":\"uuid\"}`, verifies an active lead and active staff user, updates assignment and writes `lead.assigned` to `public.audit_events` in the same transaction. It depends on the admissions workflow migration being applied. The shared-token bootstrap cannot identify the real actor, so the audit event records a null actor and `actor: shared_token`; this is not a substitute for authenticated user identity or manager/admin role checks. `POST /api/v1/leads/{lead_id}/notes` is implemented: accepts an internal `body` (1–5000 characters), writes a note and audit event transactionally, and never sends a prospect-facing message. Both write routes require the additive admissions workflow migration. The shared-token bootstrap cannot identify the real actor, so audit actor IDs are null and details mark `actor: shared_token`; per-user authentication and role checks remain required before production. `GET /api/v1/leads/{lead_id}/timeline?limit=50` is implemented with a bounded limit (1–100), newest-first ordering, and events from internal notes, conversation messages, follow-up tasks, demo bookings, and lead audit events. `page.next_cursor` is currently null; cursor pagination is not implemented. Follow-up task routes are also implemented under `/api/v1/follow-ups`: `GET /api/v1/follow-ups` supports optional `status`, `lead_id`, `due_before`, and bounded `limit`; `POST /api/v1/follow-ups` creates a task with timezone-aware `due_at`; `PATCH /api/v1/follow-ups/{task_id}` edits or snoozes pending tasks; `POST /api/v1/follow-ups/{task_id}/complete` completes a pending task. Mutations write audit events transactionally and never send outbound messages. All routes require the shared bearer token; per-user authentication/authorization is still missing. Lead merge is not implemented yet. Demo booking routes are implemented under `/api/v1/demo-bookings`: `GET` lists bounded records with optional status, lead, and time filters; `POST` creates a pending simulated booking from timezone-aware `starts_at`/`ends_at`; `POST /{booking_id}/cancel` cancels a pending simulated record. These routes never contact a calendar provider and never mark a booking confirmed. All writes create audit events. Provider-verified slots, conflict detection, rescheduling, and real calendar integration remain unimplemented.

- `POST /api/v1/leads` — implemented subset: creates a lead using `full_name`, `preferred_language`, `source`, and explicit consent booleans. Consent defaults to `false`; it sends no messages. Requires the configured shared bearer token and returns `201 {"data": ...}`. This does not yet implement contact identity fields, duplicate detection, staff ownership, or per-user authorization.
