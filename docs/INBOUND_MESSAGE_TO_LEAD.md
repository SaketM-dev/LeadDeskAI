# Automatic inbound message → lead workflow

## What it does

The FastAPI ingestion endpoint accepts a **normalized** inbound message, summarizes it with the configured Groq model, scores enquiry intent with the existing XGBoost scorer, then creates a lead or updates the existing lead for that channel identity. It stores the original message in `conversation_messages`, links it to a conversation, updates `leads.three_line_summary`, and records a `lead_events` timeline entry. Repeated provider message IDs are idempotent.

## Security and channel adapters

Endpoint: `POST /api/webhooks/inbound/{channel}`, where channel is `website`, `whatsapp`, `instagram`, `email`, or `phone`.

Every request needs `Authorization: Bearer <INBOUND_WEBHOOK_TOKEN>`. Set a long random `INBOUND_WEBHOOK_TOKEN` in the backend environment. The endpoint rejects unverified non-website provider messages unless `source_verified: true` is supplied by a trusted adapter. Do not expose the token in frontend JavaScript.

**This endpoint is a normalized ingestion boundary, not a turnkey Meta integration.** WhatsApp/Instagram require provider webhooks, signature verification, app permissions, and an adapter that converts provider payloads to this schema. Email and phone systems similarly require a trusted adapter. Never allow an arbitrary public client to set `source_verified`; only the server-side adapter should forward verified events. For a public website form/chat, use server-side validation and rate limiting.

## Environment

Repository-root `.env`:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
INBOUND_WEBHOOK_TOKEN=generate-a-long-random-secret
```

Never commit these secrets. If Groq is unavailable, the message is still persisted with an `AI summary pending` fallback, and the response indicates the summary. Retry summarization through a worker/job before treating it as complete. XGBoost scoring uses the existing synthetic training set and is explicitly experimental; do not interpret its score as a validated conversion probability or use it to deny service.

## Request example

```bash
curl -X POST http://localhost:8000/api/webhooks/inbound/website \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $INBOUND_WEBHOOK_TOKEN" \
  -d '{
    "external_message_id": "webchat-msg-001",
    "sender_id": "webchat-session-abc123",
    "sender_name": "Rahul",
    "thread_id": "webchat-session-abc123",
    "text": "I want Data Science weekend classes. What are the fees?",
    "language": "en"
  }'
```

A first message returns `status: created`; later messages from the same `sender_id` update the same lead and conversation. Duplicate `external_message_id` values return `status: duplicate`.

## Apply migration and verify

1. Back up the database and review `database/migrations/20261017_inbound_message_to_lead.sql` against the existing Supabase schema.
2. Apply the migration to the target Supabase database.
3. Configure the backend environment and restart FastAPI.
4. Send the sample request above.
5. Open Lead Management in live mode and confirm the new lead and summary are returned by the backend.
6. Check conversation history to confirm the original message was saved.
7. Test duplicate delivery by sending the same external message ID again.

The migration is additive and does not delete or rename data. It has not been applied to your Supabase project by this commit.
