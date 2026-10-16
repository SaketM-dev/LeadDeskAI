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


def test_v1_lead_creation_requires_bearer_token(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    response = client.post("/api/v1/leads", json={"full_name": "Asha Patil"})
    assert response.status_code == 401


def test_v1_lead_creation_validates_source_and_language(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    headers = {"Authorization": "Bearer test-secret"}
    bad_source = client.post("/api/v1/leads", headers=headers, json={"full_name": "Asha", "source": "unknown-channel"})
    bad_language = client.post("/api/v1/leads", headers=headers, json={"full_name": "Asha", "preferred_language": "fr"})
    assert bad_source.status_code == 422
    assert bad_language.status_code == 422


def test_v1_lead_creation_saves_explicit_consent_defaults(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def mappings(self):
            return self
        def one(self):
            return {
                "id": "lead-2",
                "full_name": "Asha Patil",
                "preferred_language": "mr",
                "stage": "new",
                "lead_score": 0,
                "first_touch_source": "website_form",
                "last_touch_source": "website_form",
                "created_at": "2026-10-17T10:00:00+00:00",
                "updated_at": "2026-10-17T10:00:00+00:00",
            }

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            assert params["full_name"] == "Asha Patil"
            assert params["marketing_consent"] is False
            assert params["whatsapp_consent"] is False
            assert params["email_consent"] is False
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/leads",
        headers={"Authorization": "Bearer test-secret"},
        json={"full_name": " Asha Patil ", "preferred_language": "mr", "source": "website_form"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["full_name"] == "Asha Patil"


def test_v1_lead_creation_returns_503_on_database_failure(monkeypatch):
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
        def begin(self):
            return BrokenConnection()

    monkeypatch.setattr(leads_module, "engine", BrokenEngine())
    response = client.post(
        "/api/v1/leads",
        headers={"Authorization": "Bearer test-secret"},
        json={"full_name": "Asha Patil"},
    )
    assert response.status_code == 503


def test_v1_lead_detail_requires_valid_uuid(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    response = client.get(
        "/api/v1/leads/not-a-uuid",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 422


def test_v1_lead_detail_returns_404_when_missing(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def mappings(self):
            return self
        def first(self):
            return None

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            assert params["lead_id"] == "11111111-1111-4111-8111-111111111111"
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.get(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 404


def test_v1_lead_detail_returns_record(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def mappings(self):
            return self
        def first(self):
            return {"id": "11111111-1111-4111-8111-111111111111", "full_name": "Asha Patil", "stage": "new"}

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.get(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Asha Patil"
