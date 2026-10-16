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


def test_versioned_health_response_is_stable():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["status"] == "healthy"


def test_v1_leads_fails_closed_when_auth_is_not_configured(monkeypatch):
    monkeypatch.delenv("LEAD_DESK_API_TOKEN", raising=False)
    response = client.get("/api/v1/leads")
    assert response.status_code == 503


def test_v1_leads_rejects_missing_or_invalid_bearer_token(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    assert client.get("/api/v1/leads").status_code == 401
    assert client.get("/api/v1/leads", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_v1_leads_returns_list_with_valid_token(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def mappings(self):
            return self
        def all(self):
            return [{"id": "lead-1", "full_name": "Asha Patil", "stage": "new"}]

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            assert params["limit"] == 10
            assert params["stage"] == "new"
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.get("/api/v1/leads?limit=10&stage=new", headers={"Authorization": "Bearer test-secret"})
    assert response.status_code == 200
    assert response.json()["data"][0]["full_name"] == "Asha Patil"
    assert response.json()["page"]["next_cursor"] is None


def test_v1_leads_rejects_unsupported_stage(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    response = client.get("/api/v1/leads?stage=unknown", headers={"Authorization": "Bearer test-secret"})
    assert response.status_code == 422


def test_v1_leads_returns_503_when_database_query_fails(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    import app.routers.v1_leads as leads_module

    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class BrokenConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            raise SQLAlchemyError("database unavailable")

    class BrokenEngine:
        def connect(self):
            return BrokenConnection()

    monkeypatch.setattr(leads_module, "engine", BrokenEngine())
    response = client.get("/api/v1/leads", headers={"Authorization": "Bearer test-secret"})
    assert response.status_code == 503
    assert "Lead data is unavailable" in response.json()["detail"]


def test_v1_leads_validates_page_size(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    response = client.get(
        "/api/v1/leads?limit=101",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 422
