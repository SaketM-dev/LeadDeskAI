"""Token-protected follow-up task endpoints.

Tasks are planning records only; these routes never send outbound messages.
"""
from datetime import datetime, timezone
from typing import Literal, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.v1_leads import require_api_token

router = APIRouter(prefix="/api/v1/follow-ups", tags=["follow-ups"])

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


@router.get("", dependencies=[Depends(require_api_token)])
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


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
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


@router.patch("/{task_id}", dependencies=[Depends(require_api_token)])
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


@router.post("/{task_id}/complete", dependencies=[Depends(require_api_token)])
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

