# Frontend Phase 1 and Phase 2

## Phase 1 — Foundation
- Next.js App Router with TypeScript and Tailwind CSS.
- Responsive shared application shell and navigation.
- Demo mode is the default; the interface visibly labels illustrative data.
- API base URL and timezone configuration.
- Central API client with network/API error handling.
- Shared API contracts and lead/dashboard service modules.
- Fictional fixtures kept separate from service logic.
- Demo login screen clearly states that authentication is not implemented.
- No secrets or production credentials are included.

## Phase 2 — Dashboard and lead management
- Dashboard metric cards, lead pipeline, search, follow-up summary and links to feature areas.
- Lead table with search, stage filtering, stage changes and local demo lead creation.
- Feature page route for lead management and additional workflow screens.
- Dashboard and lead service methods follow the endpoint contracts in docs/API_SPEC.md.
- User-facing demo notices distinguish local state from persisted API operations.

## What is not claimed
- Backend routes are not proven to exist or run.
- Authentication and role-based authorization are not connected.
- Dashboard and lead mutations are not end-to-end tested against a live API.
- Demo messaging, calendar booking and integration status are simulated.
- The interest questionnaire is not a validated psychometric assessment.
- Course facts such as fees, duration, schedules, eligibility and placement outcomes need authorized verification.

## Verification commands
Run from frontend/:

```bash
npm ci
npm run type-check
npm run lint
npm run build
```

Do not enable live mode until the backend, authentication, API response shapes, and authorization have been verified.
