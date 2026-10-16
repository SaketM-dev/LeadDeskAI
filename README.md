# AI Lead Desk

AI-powered admissions and lead management for education businesses. Unifies enquiries from WhatsApp, Instagram, calls, forms and walk-ins; supports English, Hindi, Marathi and code-switching; grounds course answers in institute-approved knowledge; schedules demos; and prioritizes follow-ups.

> **Demo data warning:** Sample course fees, durations and schedules in knowledge_base/courses.json are fictional placeholders, not verified details about TechSummitTrainers or any institute. Replace and approve before prospect-facing use.

## Shared contract
- [SPEC.md](SPEC.md) — scope, workflow, architecture, data rules and acceptance checklist.
- [docs/API_SPEC.md](docs/API_SPEC.md) — endpoint and payload contract.
- [database/schema.sql](database/schema.sql) — PostgreSQL MVP schema (18 tables).
- [knowledge_base/KNOWLEDGE_BASE.md](knowledge_base/KNOWLEDGE_BASE.md) — counselor rules and 4 sample courses.
- [knowledge_base/courses.json](knowledge_base/courses.json) — structured course facts.
- [docs/DECISIONS.md](docs/DECISIONS.md) — shared decisions before parallel coding.
- [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md) — branch and integration workflow.
- [.env.example](.env.example) — local config template; never put real secrets in Git.

## Suggested MVP stack
Frontend: Next.js + TypeScript. API: Python + FastAPI under /api/v1. DB: PostgreSQL. Worker: Redis-backed jobs for follow-ups/reminders. AI, speech, channels and calendar are adapter-based; disconnected integrations must be clearly labelled mock/simulated.

## Important product rules
Never invent fees, discounts, schedules or placement guarantees. Unsupported questions become counselor tasks. Never merge people solely on name similarity. Confirm bookings only after calendar success. Respect consent, opt-outs, quiet hours and human takeover.

This repository contains the shared specification and data contracts to begin parallel development; it is not yet a complete running application.
