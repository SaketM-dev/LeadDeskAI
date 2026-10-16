"""Conversation and message history endpoints in simulated-only mode.

Message writes are stored as simulated counselor drafts/history records. They
never contact WhatsApp, Instagram, email, phone, or any external provider.
"""
from typing import Literal, Optional
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.v1_leads import require_api_token

router = APIRouter(prefix="/api/v1", tags=["conversations"])


class ConversationCreate(BaseModel):
    channel: Literal["whatsapp", "instagram", "website", "phone", "email"]
    preferred_language: Literal["en", "hi", "mr"] = "en"


class SimulatedMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    language: Optional[Literal["en", "hi", "mr"]] = None


@router.get("/leads/{lead_id}/conversations", dependencies=[Depends(require_api_token)])
def list_lead_conversations(
    lead_id: str,
    limit: int = Query(default=50, ge=1, le=100),
):
    try:
        parsed_lead_id = str(UUID(lead_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")
    try:
        with engine.connect() as connection:
            lead = connection.execute(text(
                "SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL"
            ), {"lead_id": parsed_lead_id}).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")
            rows = connection.execute(text("""
                SELECT id, lead_id, channel, provider_mode, status, human_takeover,
                       preferred_language, consent_checked_at, created_at, updated_at
                FROM public.conversations
                WHERE lead_id = :lead_id
                ORDER BY updated_at DESC, id DESC
                LIMIT :limit
            """), {"lead_id": parsed_lead_id, "limit": limit}).mappings().all()
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Conversation history is unavailable. Apply the admissions workflow migration.")
    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}


@router.post("/leads/{lead_id}/conversations", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_conversation(lead_id: str, payload: ConversationCreate):
    """Create a simulated conversation record without connecting a channel."""
    try:
        parsed_lead_id = str(UUID(lead_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")
    try:
        with engine.begin() as connection:
            lead = connection.execute(text(
                "SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL"
            ), {"lead_id": parsed_lead_id}).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")
            row = connection.execute(text("""
                INSERT INTO public.conversations
                    (lead_id, channel, provider_mode, preferred_language)
                VALUES (:lead_id, :channel, 'simulated', :preferred_language)
                RETURNING id, lead_id, channel, provider_mode, status, human_takeover,
                          preferred_language, consent_checked_at, created_at, updated_at
            """), {
                "lead_id": parsed_lead_id,
                "channel": payload.channel,
                "preferred_language": payload.preferred_language,
            }).mappings().one()
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'conversation.created', 'lead', :lead_id, CAST(:details AS jsonb))
            """), {"lead_id": parsed_lead_id, "details": json.dumps({
                "conversation_id": str(row["id"]), "channel": payload.channel,
                "provider_mode": "simulated", "actor": "shared_token",
            })})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Conversation could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(row), "notice": "Simulated conversation only; no channel provider was contacted."}


@router.get("/conversations/{conversation_id}", dependencies=[Depends(require_api_token)])
def get_conversation(conversation_id: str):
    try:
        parsed_id = str(UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="conversation_id must be a valid UUID.")
    try:
        with engine.connect() as connection:
            row = connection.execute(text("""
                SELECT id, lead_id, channel, provider_mode, status, human_takeover,
                       preferred_language, consent_checked_at, created_at, updated_at
                FROM public.conversations WHERE id = :conversation_id
            """), {"conversation_id": parsed_id}).mappings().first()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Conversation is unavailable. Apply the admissions workflow migration.")
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"data": dict(row)}


@router.get("/conversations/{conversation_id}/messages", dependencies=[Depends(require_api_token)])
def list_conversation_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=100),
):
    try:
        parsed_id = str(UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="conversation_id must be a valid UUID.")
    try:
        with engine.connect() as connection:
            exists = connection.execute(text(
                "SELECT id FROM public.conversations WHERE id = :conversation_id"
            ), {"conversation_id": parsed_id}).mappings().first()
            if exists is None:
                raise HTTPException(status_code=404, detail="Conversation not found.")
            rows = connection.execute(text("""
                SELECT id, conversation_id, sender_type, body, language, simulated, created_at
                FROM public.conversation_messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC, id ASC
                LIMIT :limit
            """), {"conversation_id": parsed_id, "limit": limit}).mappings().all()
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Messages are unavailable. Apply the admissions workflow migration.")
    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_simulated_counselor_message(conversation_id: str, payload: SimulatedMessageCreate):
    """Store a simulated counselor message record; never dispatch it to a prospect."""
    try:
        parsed_id = str(UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="conversation_id must be a valid UUID.")
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message body cannot be blank.")
    try:
        with engine.begin() as connection:
            conversation = connection.execute(text("""
                SELECT id, lead_id, status, human_takeover, provider_mode
                FROM public.conversations WHERE id = :conversation_id FOR UPDATE
            """), {"conversation_id": parsed_id}).mappings().first()
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found.")
            if conversation["status"] != "open":
                raise HTTPException(status_code=409, detail="Conversation is closed.")
            message = connection.execute(text("""
                INSERT INTO public.conversation_messages
                    (conversation_id, sender_type, body, language, simulated)
                VALUES (:conversation_id, 'counselor', :body, :language, true)
                RETURNING id, conversation_id, sender_type, body, language, simulated, created_at
            """), {
                "conversation_id": parsed_id,
                "body": body,
                "language": payload.language,
            }).mappings().one()
            connection.execute(text("""
                UPDATE public.conversations SET updated_at = now()
                WHERE id = :conversation_id
            """), {"conversation_id": parsed_id})
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'conversation.message_recorded', 'lead', :lead_id, CAST(:details AS jsonb))
            """), {"lead_id": str(conversation["lead_id"]), "details": json.dumps({
                "conversation_id": parsed_id, "message_id": str(message["id"]),
                "simulated": True, "dispatched": False, "actor": "shared_token",
            })})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Message record could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(message), "notice": "Stored as simulated history only; no message was sent."}
