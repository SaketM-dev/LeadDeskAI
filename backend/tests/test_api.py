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


def test_database_health_returns_503_when_database_is_unavailable(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    import app.main as main_module

    class UnavailableEngine:
        def connect(self):
            raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(main_module, "engine", UnavailableEngine())
    response = client.get("/health/database")
    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]


def test_lead_list_returns_503_when_database_is_unavailable(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    import app.main as main_module

    class UnavailableEngine:
        def connect(self):
            raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(main_module, "engine", UnavailableEngine())
    response = client.get("/api/leads")
    assert response.status_code == 503
    assert "database/schema.sql" in response.json()["detail"]


def test_versioned_health_endpoint_is_database_independent():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "api_version": "v1"}


def test_readiness_returns_ready_when_database_query_succeeds(monkeypatch):
    import app.main as main_module

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            return None

    class AvailableEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(main_module, "engine", AvailableEngine())
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "connected"},
    }


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    import app.main as main_module

    class UnavailableEngine:
        def connect(self):
            raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(main_module, "engine", UnavailableEngine())
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "not_ready"
