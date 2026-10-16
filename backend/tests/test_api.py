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


def test_v1_lead_update_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    response = client.patch(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111",
        json={"stage": "qualified"},
    )
    assert response.status_code == 401


def test_v1_lead_update_validates_stage_and_empty_patch(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    headers = {"Authorization": "Bearer test-secret"}
    base = "/api/v1/leads/11111111-1111-4111-8111-111111111111"
    assert client.patch(base, headers=headers, json={"stage": "unknown"}).status_code == 422
    assert client.patch(base, headers=headers, json={}).status_code == 422


def test_v1_lead_update_returns_updated_record(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def mappings(self):
            return self
        def first(self):
            return {
                "id": "11111111-1111-4111-8111-111111111111",
                "full_name": "Asha Patil",
                "stage": "qualified",
                "marketing_consent": False,
                "whatsapp_consent": False,
                "email_consent": False,
                "do_not_contact": False,
            }

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            assert params["stage"] == "qualified"
            assert params["lead_id"] == "11111111-1111-4111-8111-111111111111"
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.patch(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111",
        headers={"Authorization": "Bearer test-secret"},
        json={"stage": "qualified"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["stage"] == "qualified"


def test_v1_lead_update_returns_404_for_missing_record(monkeypatch):
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
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.patch(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111",
        headers={"Authorization": "Bearer test-secret"},
        json={"stage": "contacted"},
    )
    assert response.status_code == 404


def test_v1_lead_assignment_validates_ids_and_auth(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    base = "/api/v1/leads/11111111-1111-4111-8111-111111111111/assign"
    assert client.post(base, json={"user_id": "22222222-2222-4222-8222-222222222222"}).status_code == 401
    response = client.post(
        "/api/v1/leads/not-a-uuid/assign",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": "not-a-uuid"},
    )
    assert response.status_code == 422


def test_v1_lead_assignment_updates_and_audits(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    executed = []

    class FakeResult:
        def __init__(self, row):
            self.row = row
        def mappings(self):
            return self
        def first(self):
            return self.row

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            sql = str(statement)
            executed.append(sql)
            if "SELECT id FROM public.leads" in sql:
                return FakeResult({"id": params["lead_id"]})
            if "SELECT id FROM public.app_users" in sql:
                return FakeResult({"id": params["user_id"]})
            if "UPDATE public.leads" in sql:
                return FakeResult({
                    "id": params["lead_id"],
                    "full_name": "Asha Patil",
                    "assigned_user_id": params["user_id"],
                    "stage": "new",
                })
            if "INSERT INTO public.audit_events" in sql:
                assert '"actor": "shared_token"' in params["details"]
                return FakeResult(None)
            raise AssertionError(f"Unexpected SQL: {sql}")

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/assign",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": "22222222-2222-4222-8222-222222222222"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["assigned_user_id"] == "22222222-2222-4222-8222-222222222222"
    assert any("INSERT INTO public.audit_events" in sql for sql in executed)


def test_v1_lead_assignment_returns_404_for_missing_staff_user(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def __init__(self, row):
            self.row = row
        def mappings(self):
            return self
        def first(self):
            return self.row

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            if "SELECT id FROM public.leads" in str(statement):
                return FakeResult({"id": params["lead_id"]})
            if "SELECT id FROM public.app_users" in str(statement):
                return FakeResult(None)
            raise AssertionError(f"Unexpected SQL: {statement}")

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/assign",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": "22222222-2222-4222-8222-222222222222"},
    )
    assert response.status_code == 404

def test_v1_lead_notes_require_auth_and_reject_blank_body(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    url = "/api/v1/leads/11111111-1111-4111-8111-111111111111/notes"
    assert client.post(url, json={"body": "Internal note"}).status_code == 401
    response = client.post(
        url,
        headers={"Authorization": "Bearer test-secret"},
        json={"body": "   "},
    )
    assert response.status_code == 422


def test_v1_lead_notes_create_internal_note_and_audit(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    statements = []

    class FakeResult:
        def __init__(self, row=None):
            self.row = row
        def mappings(self):
            return self
        def first(self):
            return self.row
        def one(self):
            return self.row

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            sql = str(statement)
            statements.append(sql)
            if "SELECT id FROM public.leads" in sql:
                return FakeResult({"id": params["lead_id"]})
            if "INSERT INTO public.lead_notes" in sql:
                assert params["body"] == "Call back tomorrow"
                return FakeResult({
                    "id": "33333333-3333-4333-8333-333333333333",
                    "lead_id": params["lead_id"],
                    "author_id": None,
                    "body": params["body"],
                })
            if "INSERT INTO public.audit_events" in sql:
                return FakeResult()
            raise AssertionError(f"Unexpected SQL: {sql}")

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/notes",
        headers={"Authorization": "Bearer test-secret"},
        json={"body": "  Call back tomorrow  "},
    )
    assert response.status_code == 201
    assert response.json()["data"]["body"] == "Call back tomorrow"
    assert any("INSERT INTO public.audit_events" in sql for sql in statements)

def test_v1_lead_timeline_validates_limit_and_uuid(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    headers = {"Authorization": "Bearer test-secret"}
    assert client.get("/api/v1/leads/not-a-uuid/timeline", headers=headers).status_code == 422
    assert client.get(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/timeline?limit=101",
        headers=headers,
    ).status_code == 422


def test_v1_lead_timeline_returns_newest_first_events(monkeypatch):
    import app.routers.v1_leads as leads_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")

    class FakeResult:
        def __init__(self, rows):
            self.rows = rows
        def mappings(self):
            return self
        def first(self):
            return self.rows[0] if self.rows else None
        def all(self):
            return self.rows

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            sql = str(statement)
            if "SELECT id FROM public.leads" in sql:
                return FakeResult([{"id": params["lead_id"]}])
            assert params["limit"] == 20
            assert "conversation_messages" in sql
            assert "lead_notes" in sql
            return FakeResult([
                {"event_id": "note-1", "event_type": "note", "summary": "Call back"},
                {"event_id": "message-1", "event_type": "message", "summary": "prospect: Hello"},
            ])

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.get(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/timeline?limit=20",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2
    assert response.json()["data"][0]["event_type"] == "note"
    assert response.json()["page"]["next_cursor"] is None


def test_v1_lead_timeline_returns_404_for_missing_lead(monkeypatch):
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
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(leads_module, "engine", FakeEngine())
    response = client.get(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/timeline",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 404

