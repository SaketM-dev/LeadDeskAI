# Frontend guide — AI Lead Desk

## Stack and layout
- Next.js App Router + TypeScript in `frontend/`.
- `app/` contains the dashboard, login screen, lead detail route, and shared feature-section route.
- `components/app-shell.tsx` provides responsive navigation and the global workspace frame.
- `components/ui.tsx` contains reusable dark Button, Card, Input, Select, Textarea, Badge, EmptyState, LoadingState, ErrorState and Modal primitives.
- `lib/api-client.ts` centralizes API requests and reports network/HTTP errors without silently switching to fixtures.
- `services/` owns API access; `fixtures/` contains fictional demo data.

## Dark design tokens
The source of truth is `app/globals.css`: CSS custom properties define page/surface/raised colors, text, muted text, borders, blue accent, status colors, radius, shadows, typography and spacing. Tailwind semantic colors in `tailwind.config.ts` refer to these tokens. The existing feature pages still contain legacy palette utilities; a compatibility layer maps many of those to dark tokens while they are migrated incrementally.

Use CSS variables or the shared UI primitives for new UI. Do not add one-off hex values to feature components. Maintain keyboard-visible focus, input labels, responsive navigation and explicit text labels for statuses.

## Demo and live modes
Set `NEXT_PUBLIC_DEMO_MODE=true` to enable fictional fixtures and local demo interactions. The workspace shows a visible **Demo data** badge. Set it to `false` only when a backend is configured. Live mode does not silently substitute fixtures after API errors; unavailable routes should surface an error or explicit unsupported-action message.

The current backend is not a complete implementation of `docs/API_SPEC.md`. At present, supported business operations are limited to lead listing and health/voice-status endpoints outside the planned `/api/v1` contract. Most counselling, aptitude, course, booking, follow-up, analytics, knowledge-management and auth operations are not fully connected end to end. Their visible pages must not be represented as production-ready integrations.

## Local checks
From `frontend/`:
```bash
npm ci
npm run type-check
npm run lint
npm run build
```
Use a configured `BACKEND_API_URL` for live requests. See `frontend/docs/BACKEND_CONNECTION.md` for backend setup and current endpoint mapping.

## Security and product invariants
- Do not put secrets in client-side environment variables or source control.
- Only approved knowledge may support course-specific claims.
- Human takeover must pause AI responses until explicit release.
- Check channel consent, opt-outs and quiet hours before any outbound side effect.
- Do not show a booking as confirmed without provider confirmation.
- Do not merge leads solely because their names look similar.
- Aptitude results are interest guidance, not admission decisions.
- Integrations without a verified provider connection must be labelled **Simulated**.
