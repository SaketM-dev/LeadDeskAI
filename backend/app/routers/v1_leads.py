"""Authenticated, read-only v1 lead listing.

The route fails closed until LEAD_DESK_API_TOKEN is configured. Replace this
shared-token bootstrap with per-user sessions and role/ownership checks before
exposing broader workflows to multiple staff members.
"""
import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
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
