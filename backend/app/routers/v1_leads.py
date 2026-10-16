"""Authenticated, read-only v1 lead listing.

The route fails closed until LEAD_DESK_API_TOKEN is configured. Replace this
shared-token bootstrap with per-user sessions and role/ownership checks before
exposing broader workflows to multiple staff members.
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

    @classmethod
    def validate_language(cls, value):
        if value not in {"en", "hi", "mr", "mixed", "unknown"}:
            raise ValueError("Unsupported preferred language.")
        return value


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
