"""Simulated demo-booking endpoints.

These records are planning-only. No calendar provider is connected, so bookings
remain pending and are always labeled simulated; this router never confirms or
creates external calendar events.
"""
from datetime import datetime, timezone
from typing import Literal, Optional
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.v1_leads import require_api_token

router = APIRouter(prefix="/api/v1/demo-bookings", tags=["demo-bookings"])


class DemoBookingCreate(BaseModel):
    lead_id: str
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Booking timestamps must include a timezone offset.")
        return value


@router.get("", dependencies=[Depends(require_api_token)])
def list_demo_bookings(
    booking_status: Optional[Literal["pending", "confirmed", "cancelled", "rescheduled"]] = Query(default=None, alias="status"),
    lead_id: Optional[str] = None,
    starts_after: Optional[datetime] = None,
    starts_before: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """List bounded booking records; timestamps are not provider-verified slots."""
    clauses = ["1 = 1"]
    params = {"limit": limit}
    if booking_status:
        clauses.append("status = :booking_status")
        params["booking_status"] = booking_status
    if lead_id:
        try:
            params["lead_id"] = str(UUID(lead_id))
        except ValueError:
            raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")
        clauses.append("lead_id = :lead_id")
    for key, value, operator in (
        ("starts_after", starts_after, ">="),
        ("starts_before", starts_before, "<="),
    ):
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise HTTPException(status_code=422, detail=f"{key} must include a timezone offset.")
            clauses.append(f"starts_at {operator} :{key}")
            params[key] = value.astimezone(timezone.utc)
    if starts_after and starts_before and starts_after > starts_before:
        raise HTTPException(status_code=422, detail="starts_after must not be later than starts_before.")

    try:
        with engine.connect() as connection:
            rows = connection.execute(text(f"""
                SELECT id, lead_id, starts_at, ends_at, status, provider_mode,
                       provider_event_id, created_at, updated_at
                FROM public.demo_bookings
                WHERE {" AND ".join(clauses)}
                ORDER BY starts_at ASC, id ASC
                LIMIT :limit
            """), params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Demo bookings are unavailable. Apply the admissions workflow migration.")
    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_demo_booking(payload: DemoBookingCreate):
    """Create a pending simulated booking; never claims calendar confirmation."""
    lead_id = str(UUID(payload.lead_id)) if _is_uuid(payload.lead_id) else None
    if lead_id is None:
        raise HTTPException(status_code=422, detail="lead_id must be a valid UUID.")
    starts_at = payload.starts_at.astimezone(timezone.utc)
    ends_at = payload.ends_at.astimezone(timezone.utc)
    if ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be later than starts_at.")

    try:
        with engine.begin() as connection:
            lead = connection.execute(text(
                "SELECT id FROM public.leads WHERE id = :lead_id AND merged_into_lead_id IS NULL"
            ), {"lead_id": lead_id}).mappings().first()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")
            booking = connection.execute(text("""
                INSERT INTO public.demo_bookings
                    (lead_id, starts_at, ends_at, status, provider_mode)
                VALUES (:lead_id, :starts_at, :ends_at, 'pending', 'simulated')
                RETURNING id, lead_id, starts_at, ends_at, status, provider_mode,
                          provider_event_id, created_at, updated_at
            """), {"lead_id": lead_id, "starts_at": starts_at, "ends_at": ends_at}).mappings().one()
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'demo_booking.created', 'lead', :lead_id, CAST(:details AS jsonb))
            """), {"lead_id": lead_id, "details": json.dumps({
                "booking_id": str(booking["id"]), "provider_mode": "simulated",
                "actor": "shared_token",
            })})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Demo booking could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(booking), "notice": "Simulated booking only; no calendar event was created or confirmed."}


@router.post("/{booking_id}/cancel", dependencies=[Depends(require_api_token)])
def cancel_demo_booking(booking_id: str):
    """Cancel a pending simulated booking; no external calendar action occurs."""
    try:
        parsed_id = str(UUID(booking_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="booking_id must be a valid UUID.")
    try:
        with engine.begin() as connection:
            booking = connection.execute(text("""
                UPDATE public.demo_bookings
                SET status = 'cancelled', updated_at = now()
                WHERE id = :booking_id AND status = 'pending' AND provider_mode = 'simulated'
                RETURNING id, lead_id, starts_at, ends_at, status, provider_mode,
                          provider_event_id, created_at, updated_at
            """), {"booking_id": parsed_id}).mappings().first()
            if booking is None:
                raise HTTPException(status_code=404, detail="Pending simulated booking not found.")
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'demo_booking.cancelled', 'lead', :lead_id,
                        jsonb_build_object('booking_id', :booking_id, 'actor', 'shared_token'))
            """), {"lead_id": str(booking["lead_id"]), "booking_id": parsed_id})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Demo booking could not be cancelled.")
    return {"data": dict(booking), "notice": "Simulated booking cancelled; no calendar provider was contacted."}


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False
