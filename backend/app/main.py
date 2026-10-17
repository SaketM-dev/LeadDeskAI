import json
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.voice import router as voice_router
from app.routers.v1_leads import router as v1_leads_router
from app.routers.v1_followups import router as v1_followups_router
from app.routers.v1_demo_bookings import router as v1_demo_bookings_router
from app.routers.v1_conversations import router as v1_conversations_router
from app.routers.v1_knowledge_base import router as v1_knowledge_base_router

app = FastAPI(
    title="AI Lead Desk API",
    description="Backend API for AI-powered admissions and lead management.",
    version="0.1.0",
)

app.include_router(voice_router)
app.include_router(v1_leads_router)
app.include_router(v1_followups_router)
app.include_router(v1_demo_bookings_router)
app.include_router(v1_conversations_router)
app.include_router(v1_knowledge_base_router)


v1_health_router = APIRouter(prefix="/api/v1", tags=["v1-health"])


@v1_health_router.get("/health")
def api_v1_health():
    """Versioned liveness endpoint; does not expose lead data or depend on the database."""
    return {"status": "healthy", "api_version": "v1"}


app.include_router(v1_health_router)



@app.get("/api/courses", tags=["courses"])
def list_demo_courses():
    """Return the clearly-labelled sample course catalogue used by the demo UI.

    These records are illustrative only. Fees, schedules, eligibility and outcomes
    must be approved by the institution before use with real prospective students.
    """
    catalog_path = Path(__file__).resolve().parents[2] / "knowledge_base" / "courses.json"
    try:
        with catalog_path.open("r", encoding="utf-8") as catalog_file:
            catalog = json.load(catalog_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="Sample course catalogue is unavailable.") from exc
    return {
        "dataset_name": catalog.get("dataset_name", "AI Lead Desk sample course knowledge base"),
        "dataset_version": catalog.get("dataset_version", 1),
        "demo_data_only": True,
        "warning": catalog.get("warning", "Illustrative sample data; verify all details before use."),
        "currency": catalog.get("currency", "INR"),
        "timezone": catalog.get("timezone", "Asia/Kolkata"),
        "courses": catalog.get("courses", []),
    }

@app.get("/")
def home():
    return {"message": "AI Lead Desk API is running", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def readiness():
    """Readiness probe: return 503 when the configured database cannot be reached."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "checks": {"database": "connected"}}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": {"database": "unavailable"}},
        )


@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()
        return {"status": "connected", "database": database_name}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check DATABASE_URL and PostgreSQL.",
        )


@app.get("/api/leads")
def list_leads():
    query = text("""
        SELECT
            id, full_name, preferred_language, stage, lead_score,
            three_line_summary, first_touch_source, last_touch_source,
            assigned_user_id, created_at, updated_at
        FROM public.leads
        WHERE merged_into_lead_id IS NULL
        ORDER BY created_at DESC
        LIMIT 100
    """)
    try:
        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Lead data is unavailable. Check DATABASE_URL and confirm database/schema.sql has been applied.",
        )
    return {"count": len(rows), "leads": [dict(row) for row in rows]}


@app.get("/api/leads/{lead_id}")
def get_lead_detail(lead_id: str):
    """Return the recorded profile for one lead without changing database data."""
    lead_query = text("""
        SELECT
            l.id, l.full_name, l.preferred_language, l.stage, l.lead_score,
            l.score_reasons, l.three_line_summary, l.assigned_user_id,
            u.full_name AS assigned_name,
            l.first_touch_source, l.last_touch_source,
            l.marketing_consent, l.whatsapp_consent, l.email_consent,
            l.do_not_contact, l.created_at, l.updated_at, l.last_inbound_at
        FROM public.leads AS l
        LEFT JOIN public.app_users AS u ON u.id = l.assigned_user_id
        WHERE l.id::text = :lead_id AND l.merged_into_lead_id IS NULL
        LIMIT 1
    """)
    identities_query = text("""
        SELECT channel, phone_e164, email_normalized, display_name,
               identity_status, created_at
        FROM public.lead_identities
        WHERE lead_id::text = :lead_id
        ORDER BY CASE WHEN identity_status = 'verified' THEN 0 ELSE 1 END,
                 created_at DESC
    """)
    try:
        with engine.connect() as connection:
            row = connection.execute(lead_query, {"lead_id": lead_id}).mappings().first()
            if row is None:
                raise HTTPException(status_code=404, detail="Lead not found.")
            identities = connection.execute(
                identities_query, {"lead_id": lead_id}
            ).mappings().all()
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not load this lead profile. Check the database connection and schema.",
        )

    lead = dict(row)
    identity_rows = [dict(item) for item in identities]
    preferred_identity = next(
        (item for item in identity_rows if item.get("identity_status") == "verified"),
        identity_rows[0] if identity_rows else {},
    )
    source = lead.get("first_touch_source") or lead.get("last_touch_source") or "other"
    summary_text = lead.get("three_line_summary") or ""
    score_reasons = lead.get("score_reasons") or []
    if isinstance(score_reasons, str):
        score_reasons = [score_reasons]
    if isinstance(score_reasons, dict):
        score_reasons = [str(value) for value in score_reasons.values()]
    summary = [line.strip() for line in summary_text.splitlines() if line.strip()]
    summary.extend(str(item) for item in score_reasons if item)
    consent = {
        "marketing": bool(lead.get("marketing_consent")),
        "whatsapp": bool(lead.get("whatsapp_consent")),
        "email": bool(lead.get("email_consent")),
        "do_not_contact": bool(lead.get("do_not_contact")),
    }
    created_at = lead.get("created_at")
    updated_at = lead.get("updated_at")
    last_inbound_at = lead.get("last_inbound_at")
    timeline = []
    if created_at:
        timeline.append({
            "id": "lead-created",
            "type": "note",
            "title": "Lead created",
            "description": "Lead record created in AI Lead Desk.",
            "occurred_at": created_at.isoformat(),
            "actor": "System",
        })
    if last_inbound_at:
        timeline.append({
            "id": "last-inbound",
            "type": "message",
            "title": "Last inbound activity",
            "description": "An inbound activity timestamp is recorded; message contents are not included in this profile endpoint.",
            "occurred_at": last_inbound_at.isoformat(),
            "actor": "System",
        })
    return {
        "id": str(lead["id"]),
        "full_name": lead["full_name"],
        "preferred_language": lead.get("preferred_language") or "unknown",
        "stage": lead.get("stage") or "new",
        "lead_score": int(lead.get("lead_score") or 0),
        "assigned_to": str(lead["assigned_user_id"]) if lead.get("assigned_user_id") else None,
        "assigned_name": lead.get("assigned_name"),
        "source": source,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "phone": preferred_identity.get("phone_e164"),
        "email": preferred_identity.get("email_normalized"),
        "course_interest": None,
        "summary": summary,
        "objections": [],
        "next_action": "Review the recorded lead details and confirm course interest with the learner.",
        "consent": consent,
        "human_takeover": False,
        "timeline": timeline,
        "identities": identity_rows,
        "last_touch_source": lead.get("last_touch_source"),
        "do_not_contact": bool(lead.get("do_not_contact")),
    }
