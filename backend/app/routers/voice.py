"""Explicit status endpoint for the optional voice/translation integration.

Voice providers are not configured by default. This router intentionally does not
pretend to transcribe or translate audio until a provider adapter is implemented.
"""
import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.get("/status")
def voice_status():
    provider = os.getenv("VOICE_PROVIDER", "not_configured").strip()
    configured = provider not in {"", "not_configured", "mock"}
    return {
        "status": "configured" if configured else "not_configured",
        "provider": provider or "not_configured",
        "message": (
            "Voice provider configuration is present; verify provider credentials and implementation."
            if configured
            else "Voice transcription and translation are not enabled. The rest of the API remains available."
        ),
    }
