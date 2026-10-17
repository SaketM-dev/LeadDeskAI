"""Endpoints for experimental XGBoost lead-intent scoring from chat enquiries."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.lead_scoring import score_transcript, training_summary

router = APIRouter(prefix="/api/lead-scoring", tags=["lead-scoring"])


class ScoreRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=20000)
    language: str = Field(default="unknown", pattern="^(en|hi|mr|mixed|unknown)$")


@router.get("/training-data")
def get_training_data_summary():
    """Expose safe aggregate metadata, not the raw synthetic conversations."""
    try:
        return training_summary()
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/score")
def score_lead(payload: ScoreRequest):
    """Score enquiry intent. This is a demo signal, not a validated conversion forecast."""
    try:
        return score_transcript(payload.transcript, payload.language)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
