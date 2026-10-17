"""Approved course catalogue and explainable, interest-based recommendations."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine

router = APIRouter(prefix="/api", tags=["courses"])

# Live approved-course endpoints use distinct paths to preserve the existing
# illustrative GET /api/courses response contract.

# This is an explainable keyword heuristic, not a trained model and not an
# estimate of admission probability. Keep labels user-facing and reviewable.
INTEREST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "data": (
        "data", "analytics", "statistic", "statistics", "mathemat", "pattern",
        "python", "analysis", "visualization", "numbers",
    ),
    "web_development": (
        "web", "website", "frontend", "front-end", "backend", "back-end",
        "software", "application", "apps", "programming", "coding", "code",
        "build apps", "developer",
    ),
    "artificial_intelligence": (
        "artificial intelligence", "machine learning", "predictive", "model",
        "algorithm", " ai ", "experiments", "science",
    ),
    "design": (
        "design", "creative", "visual", "user experience", " ux ",
        "interface", "storytelling", "research",
    ),
    "cloud_devops": (
        "cloud", "deployment", "devops", "infrastructure", "automation", "server",
    ),
}

INTEREST_LABELS = {
    "data": "data analysis and statistics",
    "web_development": "web development and programming",
    "artificial_intelligence": "AI and machine learning",
    "design": "design and user experience",
    "cloud_devops": "cloud, deployment and automation",
}

COURSE_SELECT = """
    SELECT id, code, title, description, fee_amount, fee_currency, fee_verified,
           duration_weeks, schedule_text, schedule_timezone, eligibility_text,
           status, approved_at, content_updated_at, metadata
    FROM public.courses
    WHERE status = 'approved' AND approved_at IS NOT NULL
"""


def _course_payload(row: Any) -> dict[str, Any]:
    course = dict(row)
    course["id"] = str(course["id"])
    # A stored amount must not be shown as verified unless the verification
    # flag is true. The API still exposes fee_verified for a transparent UI.
    if not course.get("fee_verified") or course.get("fee_amount") is None:
        course["fee_amount"] = None
    else:
        course["fee_amount"] = float(course["fee_amount"])
    course["fee_currency"] = (course.get("fee_currency") or "INR").strip()
    course["metadata"] = course.get("metadata") or {}
    return course


def _extract_interests(text_value: str) -> set[str]:
    normalized = f" {text_value.lower().replace('_', ' ')} "
    found: set[str] = set()
    for category, keywords in INTEREST_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            found.add(category)
    return found


def _rank_course_payloads(courses: list[dict[str, Any]], learner_text: str) -> list[dict[str, Any]]:
    """Return only supported matches, with a simple inspectable rationale."""
    learner_interests = _extract_interests(learner_text)
    if not learner_interests:
        return []

    ranked: list[dict[str, Any]] = []
    for course in courses:
        metadata = course.get("metadata") or {}
        metadata_text = " ".join(str(item) for item in metadata.values()) if isinstance(metadata, dict) else str(metadata)
        searchable = " ".join(
            str(course.get(key) or "")
            for key in ("code", "title", "description")
        ) + " " + metadata_text
        course_interests = _extract_interests(searchable)
        matching = learner_interests & course_interests
        if not matching:
            continue

        # Similarity is the share of detected learner interest categories that
        # overlap this course. It is not a probability or validated assessment.
        score = round(100 * len(matching) / len(learner_interests))
        reasons = [f"Matches the stated interest in {INTEREST_LABELS[key]}." for key in sorted(matching)]
        ranked.append({
            "course": course,
            "match_score": score,
            "score_type": "heuristic_similarity_not_admission_probability",
            "matched_interests": [INTEREST_LABELS[key] for key in sorted(matching)],
            "rationale": reasons,
        })

    ranked.sort(key=lambda item: (-item["match_score"], item["course"]["title"].lower()))
    return ranked[:5]


@router.get("/approved-courses")
def list_approved_courses():
    """List approved courses only; draft/demo-only records are never exposed."""
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(COURSE_SELECT + " ORDER BY title ASC"),
            ).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Course catalogue is unavailable. Check database connectivity and schema setup.",
        )

    courses = [_course_payload(row) for row in rows]
    return {"count": len(courses), "courses": courses}


@router.get("/approved-courses/{course_id}")
def get_approved_course(course_id: UUID):
    """Return a course only when it is approved and prospect-visible."""
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(COURSE_SELECT + " AND id = :course_id LIMIT 1"),
                {"course_id": str(course_id)},
            ).mappings().first()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Course details are unavailable. Check database connectivity and schema setup.",
        )

    if row is None:
        raise HTTPException(status_code=404, detail="Approved course not found.")
    return _course_payload(row)


@router.get("/leads/{lead_id}/recommendations")
def get_lead_course_recommendations(lead_id: UUID):
    """Recommend approved courses from a lead summary and latest completed assessment."""
    try:
        with engine.connect() as connection:
            lead = connection.execute(
                text("""
                    SELECT id, three_line_summary
                    FROM public.leads
                    WHERE id = :lead_id AND merged_into_lead_id IS NULL
                    LIMIT 1
                """),
                {"lead_id": str(lead_id)},
            ).mappings().first()

            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found.")

            assessment = connection.execute(
                text("""
                    SELECT id, goal_summary, result_summary
                    FROM public.aptitude_assessments
                    WHERE lead_id = :lead_id AND status = 'completed'
                    ORDER BY completed_at DESC NULLS LAST, started_at DESC
                    LIMIT 1
                """),
                {"lead_id": str(lead_id)},
            ).mappings().first()

            assessment_text = ""
            if assessment is not None:
                answers = connection.execute(
                    text("""
                        SELECT ar.answer_text, ar.selected_option_key, aq.skill_dimension
                        FROM public.aptitude_responses AS ar
                        JOIN public.aptitude_questions AS aq ON aq.id = ar.question_id
                        WHERE ar.assessment_id = :assessment_id
                        ORDER BY ar.response_order ASC
                    """),
                    {"assessment_id": str(assessment["id"])},
                ).mappings().all()
                assessment_text = " ".join(
                    str(value or "")
                    for answer in answers
                    for value in (answer["answer_text"], answer["selected_option_key"], answer["skill_dimension"])
                )

            course_rows = connection.execute(
                text(COURSE_SELECT + " ORDER BY title ASC"),
            ).mappings().all()
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Recommendations are unavailable. Check database connectivity and confirm database/schema.sql has been applied.",
        )

    courses = [_course_payload(row) for row in course_rows]
    learner_text = " ".join([
        str(lead.get("three_line_summary") or ""),
        str((assessment or {}).get("goal_summary") or ""),
        str((assessment or {}).get("result_summary") or ""),
        assessment_text,
    ])
    recommendations = _rank_course_payloads(courses, learner_text)
    personalized = bool(_extract_interests(learner_text))

    if not personalized:
        message = (
            "No personalized match is available yet. Add a course-interest summary or complete an "
            "aptitude assessment. Only approved courses are considered."
        )
    elif not recommendations:
        message = "No approved course currently matches the detected interests. A counselor should review options."
    else:
        message = "Recommendations are based on recorded interests and approved course descriptions. Review with a counselor."

    return {
        "lead_id": str(lead_id),
        "assessment_id": str(assessment["id"]) if assessment is not None else None,
        "personalized": personalized,
        "scoring_note": "Heuristic similarity only; not an admission probability or eligibility decision.",
        "message": message,
        "recommendations": recommendations,
    }
