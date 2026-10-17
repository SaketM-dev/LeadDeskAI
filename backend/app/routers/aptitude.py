"""Persistent, explainable aptitude-interest assessment endpoints.

Results are guidance only, not psychometric diagnoses or admissions decisions.
"""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.v1_leads import require_api_token

router = APIRouter(prefix="/api/v1/aptitude", tags=["aptitude"], dependencies=[Depends(require_api_token)])

COURSE_LABELS = {
    "realistic": "Applied Technology, Engineering and Technical Operations",
    "investigative": "Data Science, Research and Analytical Problem Solving",
    "artistic": "Design, Media and Creative Technology",
    "social": "Teaching, Counseling and People-Centered Services",
    "enterprising": "Business, Entrepreneurship and Product Leadership",
    "conventional": "Operations, Quality Assurance and Information Management",
}


def _uuid(value: str, label: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail=f"{label} must be a valid UUID.")


def _json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}
    return value or {}


class StartAssessment(BaseModel):
    lead_id: str
    language: str = Field(default="en", pattern="^(en|hi|mr|mixed)$")
    goal_summary: str = Field(default="", max_length=1000)


class AssessmentResponse(BaseModel):
    question_id: str
    selected_option_key: str
    answer_text: str | None = Field(default=None, max_length=2000)


@router.post("/assessments", status_code=201)
def start_assessment(payload: StartAssessment):
    lead_id = _uuid(payload.lead_id, "lead_id")
    try:
        with engine.begin() as conn:
            lead = conn.execute(text("SELECT id FROM public.leads WHERE id=:id AND merged_into_lead_id IS NULL"), {"id": lead_id}).first()
            if not lead:
                raise HTTPException(status_code=404, detail="Active lead not found.")
            row = conn.execute(text("""
                INSERT INTO public.aptitude_assessments (lead_id, language, goal_summary, status)
                VALUES (:lead_id, :language, :goal, 'in_progress')
                RETURNING id, lead_id, status, language, goal_summary, started_at
            """), {"lead_id": lead_id, "language": payload.language, "goal": payload.goal_summary.strip() or None}).mappings().one()
            count = conn.execute(text("SELECT count(*) FROM public.aptitude_questions WHERE is_active=true")).scalar_one()
            if not count:
                raise HTTPException(status_code=503, detail="No active aptitude questions. Apply the aptitude assessment migration.")
        return {"data": dict(row), "question_count": int(count), "notice": "Interest guidance only; not an admissions or psychometric decision."}
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Assessment storage unavailable. Verify DATABASE_URL and apply database/schema.sql plus the aptitude migration.")


@router.get("/assessments/{assessment_id}/next-question")
def next_question(assessment_id: str):
    assessment_id = _uuid(assessment_id, "assessment_id")
    try:
        with engine.connect() as conn:
            assessment = conn.execute(text("SELECT id,status FROM public.aptitude_assessments WHERE id=:id"), {"id": assessment_id}).mappings().first()
            if not assessment:
                raise HTTPException(status_code=404, detail="Assessment not found.")
            if assessment["status"] == "completed":
                return {"data": None, "completed": True}
            row = conn.execute(text("""
                SELECT q.id, q.question_key, q.version, q.question_text, q.options, q.skill_dimension,
                       (SELECT count(*) FROM public.aptitude_responses r WHERE r.assessment_id=:assessment_id) AS answered
                FROM public.aptitude_questions q
                WHERE q.is_active=true
                  AND NOT EXISTS (SELECT 1 FROM public.aptitude_responses r WHERE r.assessment_id=:assessment_id AND r.question_id=q.id)
                ORDER BY q.question_key, q.version
                LIMIT 1
            """), {"assessment_id": assessment_id}).mappings().first()
        if not row:
            return {"data": None, "completed": False, "all_answered": True}
        return {"data": {
            "id": str(row["id"]), "question_key": row["question_key"], "version": row["version"],
            "question": _json(row["question_text"]), "options": _json(row["options"]),
            "skill_dimension": row["skill_dimension"], "answered_count": int(row["answered"]),
        }, "completed": False}
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Could not load the next question. Verify the aptitude migration.")


@router.post("/assessments/{assessment_id}/responses", status_code=201)
def save_response(assessment_id: str, payload: AssessmentResponse):
    assessment_id = _uuid(assessment_id, "assessment_id")
    question_id = _uuid(payload.question_id, "question_id")
    try:
        with engine.begin() as conn:
            assessment = conn.execute(text("SELECT status FROM public.aptitude_assessments WHERE id=:id FOR UPDATE"), {"id": assessment_id}).mappings().first()
            if not assessment:
                raise HTTPException(status_code=404, detail="Assessment not found.")
            if assessment["status"] != "in_progress":
                raise HTTPException(status_code=409, detail="This assessment is already completed.")
            question = conn.execute(text("SELECT options, scoring_rubric FROM public.aptitude_questions WHERE id=:id AND is_active=true"), {"id": question_id}).mappings().first()
            if not question:
                raise HTTPException(status_code=404, detail="Active question not found.")
            options, rubric = _json(question["options"]), _json(question["scoring_rubric"])
            valid_keys = {str(o.get("key")) for o in options if isinstance(o, dict)}
            if payload.selected_option_key not in valid_keys:
                raise HTTPException(status_code=422, detail="Choose one of the listed options.")
            score = rubric.get(payload.selected_option_key, 0)
            existing = conn.execute(text("SELECT id FROM public.aptitude_responses WHERE assessment_id=:a AND question_id=:q"), {"a": assessment_id, "q": question_id}).first()
            if existing:
                raise HTTPException(status_code=409, detail="This question has already been answered.")
            order = conn.execute(text("SELECT count(*)+1 FROM public.aptitude_responses WHERE assessment_id=:a"), {"a": assessment_id}).scalar_one()
            row = conn.execute(text("""
                INSERT INTO public.aptitude_responses
                  (assessment_id, question_id, answer_text, selected_option_key, score_awarded, max_score, response_order)
                VALUES (:a,:q,:answer,:option,:score,1,:ord)
                RETURNING id, assessment_id, question_id, selected_option_key, score_awarded, response_order, created_at
            """), {"a": assessment_id, "q": question_id, "answer": payload.answer_text, "option": payload.selected_option_key, "score": score, "ord": order}).mappings().one()
            conn.execute(text("UPDATE public.aptitude_assessments SET updated_at=now() WHERE id=:id"), {"id": assessment_id})
        return {"data": dict(row)}
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Could not save the answer. Verify the aptitude migration.")


@router.post("/assessments/{assessment_id}/complete")
def complete_assessment(assessment_id: str):
    assessment_id = _uuid(assessment_id, "assessment_id")
    try:
        with engine.begin() as conn:
            assessment = conn.execute(text("SELECT id,lead_id,status FROM public.aptitude_assessments WHERE id=:id FOR UPDATE"), {"id": assessment_id}).mappings().first()
            if not assessment:
                raise HTTPException(status_code=404, detail="Assessment not found.")
            if assessment["status"] == "completed":
                row = conn.execute(text("SELECT id,lead_id,status,score,result_summary,recommended_course_ids,recommendation_rationale,completed_at FROM public.aptitude_assessments WHERE id=:id"), {"id": assessment_id}).mappings().one()
                return {"data": {**dict(row), "recommended_course_ids": _json(row["recommended_course_ids"])}, "notice": "Previously completed result returned."}
            responses = conn.execute(text("""
                SELECT r.selected_option_key, r.score_awarded
                FROM public.aptitude_responses r
                WHERE r.assessment_id=:id ORDER BY r.response_order
            """), {"id": assessment_id}).mappings().all()
            total_answered = len(responses)
            active_count = int(conn.execute(text("SELECT count(*) FROM public.aptitude_questions WHERE is_active=true")).scalar_one())
            if total_answered < active_count:
                raise HTTPException(status_code=409, detail=f"Answer all active questions before completing ({total_answered}/{active_count}).")
            dimension_points = {}
            for response in responses:
                dimension = str(response["selected_option_key"])
                dimension_points[dimension] = dimension_points.get(dimension, 0.0) + float(response["score_awarded"] or 0)
            ranked = sorted(dimension_points.items(), key=lambda item: (-item[1], item[0]))
            # Selected options express interest areas, not objectively measured ability.
            dimensions = [{"dimension": dimension, "points": points} for dimension, points in ranked]
            course_ids = [COURSE_LABELS[d] for d, _ in ranked if d in COURSE_LABELS][:3]
            score = round(100 * sum(float(r["score_awarded"] or 0) for r in responses) / max(active_count, 1), 2)
            top = dimensions[0]["dimension"] if dimensions else "general"
            summary = f"Interest profile leans toward {top.replace('_',' ')}. This reflects the options selected, not aptitude or future performance."
            rationale = "Dimension points: " + ", ".join(f"{x['dimension']}={x['points']:g}" for x in dimensions) + ". Recommendations are discussion starters; confirm goals and prerequisites with a counselor."
            row = conn.execute(text("""
                UPDATE public.aptitude_assessments
                SET status='completed', score=:score, result_summary=:summary,
                    recommended_course_ids=CAST(:courses AS jsonb), recommendation_rationale=:rationale,
                    completed_at=now()
                WHERE id=:id
                RETURNING id,lead_id,status,language,goal_summary,score,result_summary,recommended_course_ids,recommendation_rationale,started_at,completed_at
            """), {"id": assessment_id, "score": score, "summary": summary, "courses": json.dumps(course_ids), "rationale": rationale}).mappings().one()
            conn.execute(text("UPDATE public.leads SET updated_at=now() WHERE id=:id"), {"id": assessment["lead_id"]})
        result = dict(row)
        result["recommended_course_ids"] = _json(result["recommended_course_ids"])
        result["dimension_scores"] = dimensions
        return {"data": result, "notice": "Interest guidance only. This is not a validated psychometric test, an ability score, or an admissions decision."}
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Could not finalize assessment. Verify the aptitude migration.")
