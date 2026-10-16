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


@app.get("/")
def home():
    return {
        "message": "AI Lead Desk API is running",
        "version": "0.1.0",
    }


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

        return {
            "status": "connected",
            "database": database_name,
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check DATABASE_URL and PostgreSQL.",
        )

@app.get("/api/leads")
def list_leads():
    query = text("""
        SELECT
            id,
            full_name,
            preferred_language,
            stage,
            lead_score,
            three_line_summary,
            first_touch_source,
            last_touch_source,
            created_at,
            updated_at
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

    leads = [dict(row) for row in rows]

    return {
        "count": len(leads),
        "leads": leads,
    }

