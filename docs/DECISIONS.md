# Shared decisions — freeze before parallel coding

1. REST JSON API under /api/v1; FastAPI OpenAPI is the implementation reference.
2. PostgreSQL; UUID primary keys; UTC timestamps; render user-facing times in Asia/Kolkata unless prospect timezone is captured.
3. Next.js + TypeScript dashboard and Python + FastAPI backend.
4. Channels: whatsapp, instagram, phone_call, website_form, email, walk_in, manual, other.
5. Stages: new, contacted, qualified, demo_booked, demo_attended, nurturing, admitted, lost, do_not_contact.
6. Objections: fees, job_fears, family_approval, time, eligibility, location, trust, other.
7. Fee/schedule/discount/eligibility/refund/placement answers require approved current KB records; unsupported questions are escalated.
8. Exact verified identifiers may match; name/transliteration alone only suggests an identity merge.
9. Calendar-confirmed slots are real; mocks are visibly labelled simulated.
10. Ship one end-to-end path first; make unconnected providers explicit mocks rather than pretending they are live.
11. No API secrets or real prospect PII in Git or fixtures.
