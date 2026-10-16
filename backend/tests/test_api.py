from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_reports_api_running():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "AI Lead Desk API is running"


def test_health_endpoint_is_independent_of_database():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_voice_status_is_explicit_when_unconfigured(monkeypatch):
    monkeypatch.delenv("VOICE_PROVIDER", raising=False)
    response = client.get("/api/voice/status")
    assert response.status_code == 200
    assert response.json()["status"] == "not_configured"
