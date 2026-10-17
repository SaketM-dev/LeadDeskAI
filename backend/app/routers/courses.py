"""Sample course catalogue endpoint for the demo workspace.

The catalogue is illustrative. Verify all details with the institution before
using it for real admissions decisions.
"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["courses"])


def _catalog_path() -> Path:
    # backend/app/routers/courses.py -> repository root / knowledge_base/courses.json
    return Path(__file__).resolve().parents[3] / "knowledge_base" / "courses.json"


@router.get("/api/courses")
def list_courses():
    """Return the sample catalogue with explicit demo-data and verification labels."""
    try:
        with _catalog_path().open("r", encoding="utf-8") as catalog_file:
            catalog = json.load(catalog_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Sample course catalogue is unavailable. Check knowledge_base/courses.json.",
        ) from exc

    return {
        "dataset_name": catalog.get("dataset_name", "AI Lead Desk sample course knowledge base"),
        "dataset_version": catalog.get("dataset_version", 1),
        "demo_data_only": True,
        "warning": catalog.get(
            "warning",
            "Illustrative sample data; verify all details before use.",
        ),
        "currency": catalog.get("currency", "INR"),
        "timezone": catalog.get("timezone", "Asia/Kolkata"),
        "courses": catalog.get("courses", []),
    }
