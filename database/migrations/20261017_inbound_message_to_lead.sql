-- Additive migration for idempotent inbound-message ingestion.
-- Review against the target Supabase schema before applying.
BEGIN;

ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS external_thread_id text;

CREATE UNIQUE INDEX IF NOT EXISTS uq_conversations_channel_thread_lead
  ON public.conversations(channel, external_thread_id, lead_id)
  WHERE external_thread_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_conversation_messages_provider_message_id
  ON public.conversation_messages(provider_message_id)
  WHERE provider_message_id IS NOT NULL;

COMMIT;
