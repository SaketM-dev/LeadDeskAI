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

