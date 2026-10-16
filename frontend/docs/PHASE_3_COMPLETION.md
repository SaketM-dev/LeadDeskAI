# Frontend Phase 3 — Lead detail, timeline and handoff

## Delivered
- Dedicated `/leads/[leadId]` route linked from the existing leads table.
- Lead overview with pipeline stage, heuristic score, counselor assignment, language and consent snapshot.
- Counselor summary, evidence-labelled objection cards and a next-best-action panel.
- Unified timeline view for messages, stage changes, notes, bookings and follow-up suggestions.
- Local-only demo interactions for stage changes, notes, follow-up drafts and human takeover/release controls.
- Live lead list/detail reads use the currently implemented `GET /api/leads` endpoint.
- Live write actions fail closed with an explicit unavailable-endpoint error until matching backend routes exist.
- All API writes remain blocked while demo mode is enabled.
- Fictional lead-detail fixtures, clearly separated from service logic.

## Safety and limitations
- All detail fixtures are illustrative and must not be treated as actual prospects.
- Demo actions only change browser state; no server write, outbound message or task scheduling occurs.
- The inspected backend currently exposes only `GET /health`, `GET /health/database`, and `GET /api/leads`. Other endpoints in `docs/API_SPEC.md` are contracts, not proof of implemented routes.
- Lead creation, stage updates, notes, human handoff/release, follow-up tasks, conversations, courses, bookings and analytics remain unavailable in live mode until backend routes and authorization are implemented.
- Server authorization, consent/opt-out checks, audit logging, idempotency and takeover enforcement remain mandatory before enabling side-effecting actions.
- Release-to-AI requires a conversation ID from the live API response and an explicit counselor action. The demo button is not connected to a real conversation.
- Course facts that are not supported by approved current knowledge must be confirmed by an authorized counselor.
- See [BACKEND_CONNECTION.md](./BACKEND_CONNECTION.md) for environment variables, proxy routes and local verification steps.
- Build and runtime verification are not claimed by this commit. Run `npm install`, `npm run type-check`, `npm run lint` and `npm run build` from `frontend/`.

## Files
- `frontend/app/leads/[leadId]/page.tsx`
- `frontend/fixtures/lead-details.ts`
- `frontend/types/api.ts`
- `frontend/services/leads.ts`
- `frontend/app/[section]/page.tsx`
- `frontend/lib/api-client.ts`
- `frontend/next.config.js`
