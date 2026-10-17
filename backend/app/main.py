from fastapi import APIRouter, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.voice import router as voice_router
from app.routers.chatbot import router as chatbot_router
from app.routers.courses import router as courses_router
from app.routers.v1_leads import router as v1_leads_router
from app.routers.v1_followups import router as v1_followups_router
from app.routers.v1_demo_bookings import router as v1_demo_bookings_router
from app.routers.v1_conversations import router as v1_conversations_router
from app.routers.v1_knowledge_base import router as v1_knowledge_base_router
from app.routers.lead_scoring import router as lead_scoring_router

app = FastAPI(
    title="AI Lead Desk API",
    description="Backend API for AI-powered admissions and lead management.",
    version="0.1.0",
)

# Core routers
app.include_router(voice_router)
app.include_router(chatbot_router)
app.include_router(courses_router)
app.include_router(v1_leads_router)
app.include_router(v1_followups_router)
app.include_router(v1_demo_bookings_router)
app.include_router(v1_conversations_router)
app.include_router(v1_knowledge_base_router)
app.include_router(lead_scoring_router)


v1_health_router = APIRouter(prefix="/api/v1", tags=["v1-health"])


@v1_health_router.get("/health")
def api_v1_health():
    """Versioned liveness endpoint; does not expose lead data or depend on the database."""
    return {"status": "healthy", "api_version": "v1"}


app.include_router(v1_health_router)


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


@app.get("/api/dashboard/summary")
def dashboard_summary():
    """Return live dashboard counts from the same database used by lead workflows."""
    try:
        with engine.connect() as connection:
            stage_rows = connection.execute(text("""
                SELECT stage, COUNT(*) AS count
                FROM public.leads
                WHERE merged_into_lead_id IS NULL
                GROUP BY stage
            """)).mappings().all()
            totals = connection.execute(text("""
                SELECT
                    COUNT(*) AS total_leads,
                    COUNT(*) FILTER (WHERE assigned_user_id IS NULL) AS unassigned_leads,
                    COUNT(*) FILTER (WHERE stage = 'new') AS new_leads
                FROM public.leads
                WHERE merged_into_lead_id IS NULL
            """)).mappings().one()
            overdue = connection.execute(text("""
                SELECT COUNT(*)
                FROM public.follow_up_tasks
                WHERE status = 'pending' AND due_at < now()
            """)).scalar_one()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Dashboard data is unavailable. Verify DATABASE_URL and apply the admissions workflow migration.",
        )

    return {
        "stage_counts": {str(row["stage"]): int(row["count"]) for row in stage_rows if row["stage"]},
        "overdue_follow_ups": int(overdue or 0),
        "new_leads": int(totals["new_leads"] or 0),
        "unassigned_leads": int(totals["unassigned_leads"] or 0),
    }


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
