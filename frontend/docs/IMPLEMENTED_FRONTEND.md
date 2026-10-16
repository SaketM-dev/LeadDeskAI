# Frontend functionality map

This frontend implements a responsive navigation shell and demo-oriented page flows for the functions shown in the workflow diagram:

- Overview dashboard and quick links
- Lead list, search, stage filtering, local lead creation and stage changes
- Simulated counseling inbox, reply drafting, and human-takeover toggle
- Short interest assessment flow
- Course recommendation cards with explicit unverified-data warning
- Demo booking form and upcoming sample sessions
- Follow-up queue with local completion toggles
- Funnel and lead-source analytics visuals
- Knowledge article review list and approval status examples
- Integration status cards that distinguish simulated/not-configured services
- Settings and visible safety-control examples

## Important boundary

This is a frontend demo. Most interactions update local React state only and show a notice explaining that no backend operation was made. The API contract is documented in `docs/API_SPEC.md`; the page components do not imply those backend routes are implemented or connected. Replace demo data with service calls only after the FastAPI endpoints, auth, data validation, and error handling are verified.

Course fees, schedules, durations, eligibility and placement claims must not be invented. The demo course cards deliberately avoid asserting specific factual fees or schedules.
