"""Token-protected v1 lead endpoints.

The shared token is a temporary bootstrap, not per-user authentication. Add
sessions, role/ownership checks, and audit logging before broader production use.
"""
import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


def require_api_token(authorization: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("LEAD_DESK_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="API authentication is not configured.")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Valid bearer token required.")


@router.get("", dependencies=[Depends(require_api_token)])
def list_leads(
    q: Optional[str] = Query(default=None, min_length=1, max_length=100),
    stage: Optional[str] = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Return a bounded lead list; no write operations are exposed by this router."""
    clauses = ["merged_into_lead_id IS NULL"]
    params = {"limit": limit}
    if q:
        clauses.append("full_name ILIKE :query")
        params["query"] = f"%{q.strip()}%"
    if stage:
        allowed_stages = {
            "new", "contacted", "qualified", "demo_booked", "demo_attended",
            "nurturing", "admitted", "lost", "do_not_contact",
        }
        if stage not in allowed_stages:
            raise HTTPException(status_code=422, detail="Unsupported lead stage.")
        clauses.append("stage = :stage")
        params["stage"] = stage

    query = text(f"""
        SELECT id, full_name, preferred_language, stage, lead_score,
               three_line_summary, first_touch_source, last_touch_source,
               created_at, updated_at
        FROM public.leads
        WHERE {" AND ".join(clauses)}
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    try:
        with engine.connect() as connection:
            rows = connection.execute(query, params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Lead data is unavailable. Verify DATABASE_URL and database/schema.sql.",
        )
    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}

class LeadCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    preferred_language: str = Field(default="unknown")
    source: str = Field(default="manual", max_length=40)
    marketing_consent: bool = False
    whatsapp_consent: bool = False
    email_consent: bool = False


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_lead(payload: LeadCreate):
    """Create a lead with explicit consent defaults; no outbound messages are sent."""
    name = payload.full_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="full_name cannot be blank.")
    if payload.preferred_language not in {"en", "hi", "mr", "mixed", "unknown"}:
        raise HTTPException(status_code=422, detail="Unsupported preferred_language.")
    allowed_sources = {"whatsapp", "instagram", "phone_call", "website_form", "email", "walk_in", "manual", "other"}
    if payload.source not in allowed_sources:
        raise HTTPException(status_code=422, detail="Unsupported source.")
    statement = text("""
        INSERT INTO public.leads
          (full_name, preferred_language, first_touch_source, last_touch_source,
           marketing_consent, whatsapp_consent, email_consent)
        VALUES
          (:full_name, :preferred_language, :source, :source,
           :marketing_consent, :whatsapp_consent, :email_consent)
        RETURNING id, full_name, preferred_language, stage, lead_score,
                  first_touch_source, last_touch_source, created_at, updated_at
    """)
    try:
        with engine.begin() as connection:
            row = connection.execute(statement, {
                "full_name": name,
                "preferred_language": payload.preferred_language,
                "source": payload.source,
                "marketing_consent": payload.marketing_consent,
                "whatsapp_consent": payload.whatsapp_consent,
                "email_consent": payload.email_consent,
            }).mappings().one()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Lead could not be saved. Verify DATABASE_URL and database/schema.sql.")
    return {"data": dict(row)}



@router.get("/{lead_id}", dependencies=[Depends(require_api_token)])
def get_lead(lead_id: str):
    """Return one active lead by UUID without exposing merged duplicate records."""
    from uuid import UUID

    try:
        parsed_id = UUID(lead_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")

    statement = text("""
        SELECT id, full_name, preferred_language, stage, lead_score,
               three_line_summary, first_touch_source, last_touch_source,
               marketing_consent, whatsapp_consent, email_consent,
               do_not_contact, assigned_user_id, created_at, updated_at
        FROM public.leads
        WHERE id = :lead_id AND merged_into_lead_id IS NULL
    """)
    try:
        with engine.connect() as connection:
            row = connection.execute(statement, {"lead_id": str(parsed_id)}).mappings().first()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Lead data is unavailable. Verify DATABASE_URL and database/schema.sql.",
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return {"data": dict(row)}


class LeadUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    preferred_language: Optional[str] = None
    stage: Optional[str] = None
    marketing_consent: Optional[bool] = None
    whatsapp_consent: Optional[bool] = None
    email_consent: Optional[bool] = None
    do_not_contact: Optional[bool] = None


@router.patch("/{lead_id}", dependencies=[Depends(require_api_token)])
def update_lead(lead_id: str, payload: LeadUpdate):
    """Update explicitly supplied lead fields; no messages are sent by this operation."""
    from uuid import UUID

    try:
        parsed_id = str(UUID(lead_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")

    changes = payload.dict(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one field to update.")

    allowed_stages = {
        "new", "contacted", "qualified", "demo_booked", "demo_attended",
        "nurturing", "admitted", "lost", "do_not_contact",
    }
    allowed_languages = {"en", "hi", "mr", "mixed", "unknown"}
    if "full_name" in changes:
        changes["full_name"] = changes["full_name"].strip()
        if not changes["full_name"]:
            raise HTTPException(status_code=422, detail="full_name cannot be blank.")
    if "stage" in changes and changes["stage"] not in allowed_stages:
        raise HTTPException(status_code=422, detail="Unsupported lead stage.")
    if "preferred_language" in changes and changes["preferred_language"] not in allowed_languages:
        raise HTTPException(status_code=422, detail="Unsupported preferred_language.")

    # Column names come only from the fixed allowlist below, never from user input.
    column_allowlist = {
        "full_name", "preferred_language", "stage", "marketing_consent",
        "whatsapp_consent", "email_consent", "do_not_contact",
    }
    if not set(changes).issubset(column_allowlist):
        raise HTTPException(status_code=422, detail="Unsupported update field.")
    assignments = ", ".join(f"{column} = :{column}" for column in changes)
    changes["lead_id"] = parsed_id
    statement = text(f"""
        UPDATE public.leads
        SET {assignments}, updated_at = now()
        WHERE id = :lead_id AND merged_into_lead_id IS NULL
        RETURNING id, full_name, preferred_language, stage, lead_score,
                  first_touch_source, last_touch_source, marketing_consent,
                  whatsapp_consent, email_consent, do_not_contact,
                  assigned_user_id, created_at, updated_at
    """)
    try:
        with engine.begin() as connection:
            row = connection.execute(statement, changes).mappings().first()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Lead could not be updated. Verify DATABASE_URL and database/schema.sql.")
    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return {"data": dict(row)}

class LeadAssignment(BaseModel):
    user_id: str = Field(min_length=36, max_length=36)


@router.post("/{lead_id}/assign", dependencies=[Depends(require_api_token)])
def assign_lead(lead_id: str, payload: LeadAssignment):
    """Assign an active lead to an active staff user and record an audit event."""
    import json
    from uuid import UUID

    try:
        parsed_lead_id = str(UUID(lead_id))
        parsed_user_id = str(UUID(payload.user_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id and user_id must be valid UUIDs.")

    try:
        with engine.begin() as connection:
            lead = connection.execute(
                text("SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL FOR UPDATE"),
                {"lead_id": parsed_lead_id},
            ).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")

            user = connection.execute(
                text("SELECT id FROM public.app_users WHERE id = :user_id AND is_active = true"),
                {"user_id": parsed_user_id},
            ).mappings().first()
            if user is None:
                raise HTTPException(status_code=404, detail="Active staff user not found.")

            updated = connection.execute(text("""
                UPDATE public.leads
                SET assigned_user_id = :user_id, updated_at = now()
                WHERE id = :lead_id AND merged_into_lead_id IS NULL
                RETURNING id, full_name, preferred_language, stage, assigned_user_id, updated_at
            """), {"lead_id": parsed_lead_id, "user_id": parsed_user_id}).mappings().first()
            connection.execute(text("""
                INSERT INTO public.audit_events
                    (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'lead.assigned', 'lead', :lead_id, CAST(:details AS jsonb))
            """), {
                "lead_id": parsed_lead_id,
                "details": json.dumps({"assigned_to": parsed_user_id, "actor": "shared_token"}),
            })
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Assignment could not be saved. Apply the admissions workflow migration and verify the database.",
        )

    return {"data": dict(updated)}

class LeadNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


@router.post("/{lead_id}/notes", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_lead_note(lead_id: str, payload: LeadNoteCreate):
    """Add an internal note without sending a prospect-facing message."""
    from uuid import UUID

    try:
        parsed_lead_id = str(UUID(lead_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Note body cannot be blank.")

    try:
        with engine.begin() as connection:
            lead = connection.execute(
                text("SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL FOR UPDATE"),
                {"lead_id": parsed_lead_id},
            ).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")

            note = connection.execute(text("""
                INSERT INTO public.lead_notes (lead_id, author_id, body)
                VALUES (:lead_id, NULL, :body)
                RETURNING id, lead_id, author_id, body, created_at
            """), {"lead_id": parsed_lead_id, "body": body}).mappings().one()
            connection.execute(text("""
                INSERT INTO public.audit_events
                    (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'lead.note_added', 'lead', :lead_id, CAST(:details AS jsonb))
            """), {"lead_id": parsed_lead_id, "details": '{"actor":"shared_token"}'})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Note could not be saved. Apply the admissions workflow migration and verify the database.",
        )

    return {"data": dict(note)}

@router.get("/{lead_id}/timeline", dependencies=[Depends(require_api_token)])
def get_lead_timeline(
    lead_id: str,
    limit: int = Query(default=50, ge=1, le=100),
):
    """Return a bounded, newest-first timeline across notes, messages, tasks, bookings and audit events."""
    from uuid import UUID

    try:
        parsed_lead_id = str(UUID(lead_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")

    statement = text("""
        WITH timeline AS (
            SELECT n.id::text AS event_id, 'note'::text AS event_type,
                   n.body AS summary, n.created_at AS occurred_at,
                   jsonb_build_object('author_id', n.author_id) AS details
            FROM public.lead_notes n
            WHERE n.lead_id = :lead_id
            UNION ALL
            SELECT m.id::text, 'message'::text,
                   m.sender_type || ': ' || left(m.body, 500), m.created_at,
                   jsonb_build_object('conversation_id', m.conversation_id,
                                      'language', m.language, 'simulated', m.simulated)
            FROM public.conversation_messages m
            JOIN public.conversations c ON c.id = m.conversation_id
            WHERE c.lead_id = :lead_id
            UNION ALL
            SELECT t.id::text, 'follow_up'::text, t.title, t.created_at,
                   jsonb_build_object('status', t.status, 'priority', t.priority,
                                      'due_at', t.due_at, 'assigned_to', t.assigned_to)
            FROM public.follow_up_tasks t
            WHERE t.lead_id = :lead_id
            UNION ALL
            SELECT b.id::text, 'demo_booking'::text, 'Demo booking: ' || b.status,
                   b.created_at,
                   jsonb_build_object('starts_at', b.starts_at, 'ends_at', b.ends_at,
                                      'status', b.status, 'provider_mode', b.provider_mode)
            FROM public.demo_bookings b
            WHERE b.lead_id = :lead_id
            UNION ALL
            SELECT a.id::text, a.event_type, a.event_type, a.created_at, a.details
            FROM public.audit_events a
            WHERE a.entity_type = 'lead' AND a.entity_id = CAST(:lead_id AS uuid)
        )
        SELECT event_id, event_type, summary, occurred_at, details
        FROM timeline
        ORDER BY occurred_at DESC, event_id DESC
        LIMIT :limit
    """)
    try:
        with engine.connect() as connection:
            lead = connection.execute(
                text("SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL"),
                {"lead_id": parsed_lead_id},
            ).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")
            rows = connection.execute(
                statement, {"lead_id": parsed_lead_id, "limit": limit}
            ).mappings().all()
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Lead timeline is unavailable. Apply the admissions workflow migration and verify the database.",
        )

    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}

from datetime import datetime, timezone
from typing import Literal
from pydantic import field_validator


class FollowUpCreate(BaseModel):
    lead_id: str
    title: str = Field(min_length=1, max_length=240)
    suggested_message: Optional[str] = Field(default=None, max_length=5000)
    priority: Literal["low", "medium", "high"] = "medium"
    due_at: datetime
    assigned_to: Optional[str] = None

    @field_validator("due_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include a timezone offset.")
        return value


class FollowUpUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=240)
    suggested_message: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


@router.get("/../follow-ups", dependencies=[Depends(require_api_token)])
def list_follow_ups(
    task_status: Optional[Literal["pending", "completed", "cancelled"]] = Query(default=None, alias="status"),
    lead_id: Optional[str] = None,
    due_before: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """List follow-up tasks with bounded filters; no task triggers outbound messages."""
    from uuid import UUID

    clauses = ["1 = 1"]
    params = {"limit": limit}
    if task_status:
        clauses.append("status = :task_status")
        params["task_status"] = task_status
    if lead_id:
        try:
            params["lead_id"] = str(UUID(lead_id))
        except ValueError:
            raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")
        clauses.append("lead_id = :lead_id")
    if due_before:
        if due_before.tzinfo is None or due_before.utcoffset() is None:
            raise HTTPException(status_code=422, detail="due_before must include a timezone offset.")
        clauses.append("due_at <= :due_before")
        params["due_before"] = due_before.astimezone(timezone.utc)

    try:
        with engine.connect() as connection:
            rows = connection.execute(text(f"""
                SELECT id, lead_id, assigned_to, title, suggested_message, priority,
                       due_at, status, completed_at, created_at, updated_at
                FROM public.follow_up_tasks
                WHERE {" AND ".join(clauses)}
                ORDER BY due_at ASC, id ASC
                LIMIT :limit
            """), params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Follow-up tasks are unavailable. Apply the admissions workflow migration.")
    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}


@router.post("/../follow-ups", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_follow_up(payload: FollowUpCreate):
    """Create a follow-up task; planning never sends a message automatically."""
    from uuid import UUID
    import json

    try:
        lead_id = str(UUID(payload.lead_id))
        assigned_to = str(UUID(payload.assigned_to)) if payload.assigned_to else None
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_id and assigned_to must be valid UUIDs.")

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="title cannot be blank.")
    due_at = payload.due_at.astimezone(timezone.utc)
    try:
        with engine.begin() as connection:
            lead = connection.execute(text(
                "SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL"
            ), {"lead_id": lead_id}).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")
            if assigned_to:
                user = connection.execute(text(
                    "SELECT id FROM public.app_users WHERE id = :user_id AND is_active = true"
                ), {"user_id": assigned_to}).mappings().first()
                if user is None:
                    raise HTTPException(status_code=404, detail="Active staff user not found.")
            task = connection.execute(text("""
                INSERT INTO public.follow_up_tasks
                    (lead_id, assigned_to, title, suggested_message, priority, due_at)
                VALUES (:lead_id, :assigned_to, :title, :suggested_message, :priority, :due_at)
                RETURNING id, lead_id, assigned_to, title, suggested_message, priority,
                          due_at, status, completed_at, created_at, updated_at
            """), {
                "lead_id": lead_id, "assigned_to": assigned_to, "title": title,
                "suggested_message": payload.suggested_message,
                "priority": payload.priority, "due_at": due_at,
            }).mappings().one()
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'follow_up.created', 'lead', :lead_id, CAST(:details AS jsonb))
            """), {"lead_id": lead_id, "details": json.dumps({"task_id": str(task["id"]), "actor": "shared_token"})})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Follow-up task could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(task)}


@router.patch("/../follow-ups/{task_id}", dependencies=[Depends(require_api_token)])
def update_follow_up(task_id: str, payload: FollowUpUpdate):
    """Edit or snooze a follow-up task without executing it."""
    from uuid import UUID

    try:
        parsed_task_id = str(UUID(task_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="task_id must be a valid UUID.")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one field to update.")
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if not changes["title"]:
            raise HTTPException(status_code=422, detail="title cannot be blank.")
    if "due_at" in changes:
        value = changes["due_at"]
        if value is None or value.tzinfo is None or value.utcoffset() is None:
            raise HTTPException(status_code=422, detail="due_at must include a timezone offset.")
        changes["due_at"] = value.astimezone(timezone.utc)
    if "assigned_to" in changes:
        if changes["assigned_to"] is None:
            pass
        else:
            try:
                changes["assigned_to"] = str(UUID(changes["assigned_to"]))
            except ValueError:
                raise HTTPException(status_code=422, detail="assigned_to must be a valid UUID.")

    allowed = {"title", "suggested_message", "priority", "due_at", "assigned_to"}
    if not set(changes).issubset(allowed):
        raise HTTPException(status_code=422, detail="Unsupported task field.")
    assignments = ", ".join(f"{key} = :{key}" for key in changes)
    changes["task_id"] = parsed_task_id
    try:
        with engine.begin() as connection:
            if changes.get("assigned_to"):
                user = connection.execute(text(
                    "SELECT id FROM public.app_users WHERE id = :user_id AND is_active = true"
                ), {"user_id": changes["assigned_to"]}).mappings().first()
                if user is None:
                    raise HTTPException(status_code=404, detail="Active staff user not found.")
            task = connection.execute(text(f"""
                UPDATE public.follow_up_tasks
                SET {assignments}, updated_at = now()
                WHERE id = :task_id AND status = 'pending'
                RETURNING id, lead_id, assigned_to, title, suggested_message, priority,
                          due_at, status, completed_at, created_at, updated_at
            """), changes).mappings().first()
            if task is None:
                raise HTTPException(status_code=404, detail="Pending follow-up task not found.")
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'follow_up.updated', 'lead', :lead_id,
                        jsonb_build_object('task_id', :task_id, 'actor', 'shared_token'))
            """), {"lead_id": str(task["lead_id"]), "task_id": parsed_task_id})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Follow-up task could not be updated. Apply the admissions workflow migration.")
    return {"data": dict(task)}


@router.post("/../follow-ups/{task_id}/complete", dependencies=[Depends(require_api_token)])
def complete_follow_up(task_id: str):
    """Complete a pending task and audit the change; does not send any message."""
    from uuid import UUID

    try:
        parsed_task_id = str(UUID(task_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="task_id must be a valid UUID.")
    try:
        with engine.begin() as connection:
            task = connection.execute(text("""
                UPDATE public.follow_up_tasks
                SET status = 'completed', completed_at = now(), updated_at = now()
                WHERE id = :task_id AND status = 'pending'
                RETURNING id, lead_id, assigned_to, title, suggested_message, priority,
                          due_at, status, completed_at, created_at, updated_at
            """), {"task_id": parsed_task_id}).mappings().first()
            if task is None:
                raise HTTPException(status_code=404, detail="Pending follow-up task not found.")
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'follow_up.completed', 'lead', :lead_id,
                        jsonb_build_object('task_id', :task_id, 'actor', 'shared_token'))
            """), {"lead_id": str(task["lead_id"]), "task_id": parsed_task_id})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Follow-up task could not be completed. Apply the admissions workflow migration.")
    return {"data": dict(task)}

