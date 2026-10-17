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

def test_v1_follow_up_creation_requires_auth_and_timezone(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    url = "/api/v1/follow-ups"
    body = {
        "lead_id": "11111111-1111-4111-8111-111111111111",
        "title": "Call prospect",
        "due_at": "2026-10-20T10:00:00+05:30",
    }
    assert client.post(url, json=body).status_code == 401
    headers = {"Authorization": "Bearer test-secret"}
    no_timezone = {**body, "due_at": "2026-10-20T10:00:00"}
    assert client.post(url, headers=headers, json=no_timezone).status_code == 422


def test_v1_follow_up_creation_writes_task_and_audit(monkeypatch):
    import app.routers.v1_followups as followups_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    statements = []

    class FakeResult:
        def __init__(self, row=None, rows=None):
            self.row, self.rows = row, rows or []
        def mappings(self):
            return self
        def first(self):
            return self.row
        def one(self):
            return self.row
        def all(self):
            return self.rows

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            sql = str(statement)
            statements.append(sql)
            if "SELECT id FROM public.leads" in sql:
                return FakeResult(row={"id": params["lead_id"]})
            if "INSERT INTO public.follow_up_tasks" in sql:
                assert params["title"] == "Call prospect"
                assert params["priority"] == "high"
                return FakeResult(row={
                    "id": "33333333-3333-4333-8333-333333333333",
                    "lead_id": params["lead_id"],
                    "title": params["title"],
                    "priority": params["priority"],
                    "status": "pending",
                })
            if "INSERT INTO public.audit_events" in sql:
                assert "follow_up.created" in sql
                return FakeResult()
            raise AssertionError(f"Unexpected SQL: {sql}")

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(followups_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/follow-ups",
        headers={"Authorization": "Bearer test-secret"},
        json={
            "lead_id": "11111111-1111-4111-8111-111111111111",
            "title": " Call prospect ",
            "priority": "high",
            "due_at": "2026-10-20T10:00:00+05:30",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["title"] == "Call prospect"
    assert any("INSERT INTO public.audit_events" in sql for sql in statements)


def test_v1_follow_up_list_validates_limit(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    response = client.get(
        "/api/v1/follow-ups?limit=101",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 422


def test_v1_follow_up_completion_is_audited(monkeypatch):
    import app.routers.v1_followups as followups_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    statements = []

    class FakeResult:
        def mappings(self):
            return self
        def first(self):
            return {
                "id": "33333333-3333-4333-8333-333333333333",
                "lead_id": "11111111-1111-4111-8111-111111111111",
                "status": "completed",
            }

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            sql = str(statement)
            statements.append(sql)
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(followups_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/follow-ups/33333333-3333-4333-8333-333333333333/complete",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
    assert any("follow_up.completed" in sql for sql in statements)



def test_demo_booking_creation_requires_auth_and_timezone(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    body = {
        "lead_id": "11111111-1111-4111-8111-111111111111",
        "starts_at": "2026-10-20T10:00:00+05:30",
        "ends_at": "2026-10-20T11:00:00+05:30",
    }
    assert client.post("/api/v1/demo-bookings", json=body).status_code == 401
    headers = {"Authorization": "Bearer test-secret"}
    body["starts_at"] = "2026-10-20T10:00:00"
    assert client.post("/api/v1/demo-bookings", headers=headers, json=body).status_code == 422


def test_demo_booking_creation_is_pending_and_simulated(monkeypatch):
    import app.routers.v1_demo_bookings as bookings_module
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
            if "INSERT INTO public.demo_bookings" in sql:
                assert "'pending', 'simulated'" in sql
                return FakeResult({
                    "id": "44444444-4444-4444-8444-444444444444",
                    "lead_id": params["lead_id"],
                    "status": "pending",
                    "provider_mode": "simulated",
                })
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(bookings_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/demo-bookings",
        headers={"Authorization": "Bearer test-secret"},
        json={
            "lead_id": "11111111-1111-4111-8111-111111111111",
            "starts_at": "2026-10-20T10:00:00+05:30",
            "ends_at": "2026-10-20T11:00:00+05:30",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "pending"
    assert response.json()["data"]["provider_mode"] == "simulated"
    assert "no calendar event was created" in response.json()["notice"]
    assert any("INSERT INTO public.audit_events" in sql for sql in statements)


def test_demo_booking_rejects_invalid_time_range_and_list_limit(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    headers = {"Authorization": "Bearer test-secret"}
    response = client.post(
        "/api/v1/demo-bookings",
        headers=headers,
        json={
            "lead_id": "11111111-1111-4111-8111-111111111111",
            "starts_at": "2026-10-20T11:00:00+05:30",
            "ends_at": "2026-10-20T10:00:00+05:30",
        },
    )
    assert response.status_code == 422
    assert client.get("/api/v1/demo-bookings?limit=101", headers=headers).status_code == 422


def test_demo_booking_cancellation_is_audited(monkeypatch):
    import app.routers.v1_demo_bookings as bookings_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    statements = []

    class FakeResult:
        def mappings(self):
            return self
        def first(self):
            return {
                "id": "44444444-4444-4444-8444-444444444444",
                "lead_id": "11111111-1111-4111-8111-111111111111",
                "status": "cancelled",
                "provider_mode": "simulated",
            }

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, traceback):
            return False
        def execute(self, statement, params):
            sql = str(statement)
            statements.append(sql)
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(bookings_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/demo-bookings/44444444-4444-4444-8444-444444444444/cancel",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled"
    assert any("demo_booking.cancelled" in sql for sql in statements)


def test_conversation_creation_requires_auth_and_creates_simulated_record(monkeypatch):
    import app.routers.v1_conversations as conversations_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    lead_id = "11111111-1111-4111-8111-111111111111"
    body = {"channel": "whatsapp", "preferred_language": "mr"}
    assert client.post(f"/api/v1/leads/{lead_id}/conversations", json=body).status_code == 401

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
            if "SELECT id FROM public.leads" in sql:
                return FakeResult({"id": lead_id})
            if "INSERT INTO public.conversations" in sql:
                assert "'simulated'" in sql
                return FakeResult({
                    "id": "55555555-5555-4555-8555-555555555555",
                    "lead_id": lead_id, "channel": "whatsapp",
                    "provider_mode": "simulated", "preferred_language": "mr",
                })
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(conversations_module, "engine", FakeEngine())
    response = client.post(
        f"/api/v1/leads/{lead_id}/conversations",
        headers={"Authorization": "Bearer test-secret"},
        json=body,
    )
    assert response.status_code == 201
    assert response.json()["data"]["provider_mode"] == "simulated"
    assert "no channel provider was contacted" in response.json()["notice"]


def test_conversation_message_is_stored_simulated_and_never_dispatched(monkeypatch):
    import app.routers.v1_conversations as conversations_module
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
            if "SELECT id, lead_id, status, human_takeover" in sql:
                return FakeResult({
                    "id": "55555555-5555-4555-8555-555555555555",
                    "lead_id": "11111111-1111-4111-8111-111111111111",
                    "status": "open", "human_takeover": True,
                    "provider_mode": "simulated",
                })
            if "INSERT INTO public.conversation_messages" in sql:
                assert "'counselor'" in sql
                assert "true" in sql.lower()
                assert params["body"] == "Fee details are being checked."
                return FakeResult({
                    "id": "66666666-6666-4666-8666-666666666666",
                    "conversation_id": "55555555-5555-4555-8555-555555555555",
                    "sender_type": "counselor", "body": params["body"],
                    "simulated": True,
                })
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(conversations_module, "engine", FakeEngine())
    response = client.post(
        "/api/v1/conversations/55555555-5555-4555-8555-555555555555/messages",
        headers={"Authorization": "Bearer test-secret"},
        json={"body": " Fee details are being checked. ", "language": "en"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["simulated"] is True
    assert "no message was sent" in response.json()["notice"]
    assert any("conversation.message_recorded" in sql for sql in statements)


def test_conversation_routes_validate_ids_limits_and_blank_messages(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    headers = {"Authorization": "Bearer test-secret"}
    assert client.get("/api/v1/conversations/not-a-uuid", headers=headers).status_code == 422
    assert client.get(
        "/api/v1/leads/11111111-1111-4111-8111-111111111111/conversations?limit=101",
        headers=headers,
    ).status_code == 422
    response = client.post(
        "/api/v1/conversations/55555555-5555-4555-8555-555555555555/messages",
        headers=headers,
        json={"body": "   "},
    )
    # Validation is performed after stripping so whitespace-only messages are rejected.
    assert response.status_code in {404, 422}



def test_conversation_takeover_and_release_are_audited(monkeypatch):
    import app.routers.v1_conversations as conversations_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    statements = []
    takeover_active = {"value": False}

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
            if "SELECT id, lead_id, status, human_takeover" in sql:
                return FakeResult({
                    "id": "55555555-5555-4555-8555-555555555555",
                    "lead_id": "11111111-1111-4111-8111-111111111111",
                    "status": "open",
                    "human_takeover": takeover_active["value"],
                })
            if "UPDATE public.conversations" in sql:
                takeover_active["value"] = params.get("human_takeover", "human_takeover = true" in sql)
                return FakeResult({
                    "id": "55555555-5555-4555-8555-555555555555",
                    "lead_id": "11111111-1111-4111-8111-111111111111",
                    "channel": "website", "provider_mode": "simulated",
                    "status": "open", "human_takeover": takeover_active["value"],
                })
            return FakeResult()

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(conversations_module, "engine", FakeEngine())
    headers = {"Authorization": "Bearer test-secret"}
    takeover = client.post(
        "/api/v1/conversations/55555555-5555-4555-8555-555555555555/takeover",
        headers=headers,
    )
    assert takeover.status_code == 200
    assert takeover.json()["data"]["human_takeover"] is True
    assert "does not authenticate a specific counselor" in takeover.json()["notice"]
    release = client.post(
        "/api/v1/conversations/55555555-5555-4555-8555-555555555555/release-to-ai",
        headers=headers,
    )
    assert release.status_code == 200
    assert release.json()["data"]["human_takeover"] is False
    assert "no messages were sent" in release.json()["notice"]
    assert any("conversation.human_takeover_started" in sql for sql in statements)
    assert any("conversation.human_takeover_released" in sql for sql in statements)


def test_conversation_takeover_routes_validate_ids_and_auth(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    url = "/api/v1/conversations/not-a-uuid/takeover"
    assert client.post(url, headers={"Authorization": "Bearer test-secret"}).status_code == 422
    assert client.post("/api/v1/conversations/55555555-5555-4555-8555-555555555555/takeover").status_code == 401

def test_knowledge_article_creation_saves_draft_and_version(monkeypatch):
    import app.routers.v1_knowledge_base as kb_module
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    statements = []
    class FakeResult:
        def mappings(self): return self
        def one(self):
            return {"id":"77777777-7777-4777-8777-777777777777","kind":"faq","title":"Fees","body":"Ask admissions","status":"draft","version":1}
    class FakeConnection:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, traceback): return False
        def execute(self, statement, params):
            statements.append(str(statement))
            if "INSERT INTO public.knowledge_articles" in str(statement): return FakeResult()
            return FakeResult()
    class FakeEngine:
        def begin(self): return FakeConnection()
    monkeypatch.setattr(kb_module, "engine", FakeEngine())
    response = client.post("/api/v1/knowledge-base/documents",
        headers={"Authorization":"Bearer test-secret"},
        json={"kind":"faq","title":" Fees ","body":" Ask admissions "})
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "draft"
    assert "not approved for AI use" in response.json()["notice"]
    assert any("knowledge_article_versions" in sql for sql in statements)
    assert any("audit_events" in sql for sql in statements)


def test_knowledge_base_requires_auth_and_validates_content(monkeypatch):
    monkeypatch.setenv("LEAD_DESK_API_TOKEN", "test-secret")
    assert client.get("/api/v1/knowledge-base/documents").status_code == 401
    response = client.post("/api/v1/knowledge-base/documents",
        headers={"Authorization":"Bearer test-secret"},
        json={"kind":"faq","title":"  ","body":"body"})
    assert response.status_code == 422


def test_course_catalogue_endpoint_returns_labeled_sample_data():
    response = client.get("/api/courses")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo_data_only"] is True
    assert payload["courses"]
    assert any(course.get("title") == "UI/UX Design Fundamentals" for course in payload["courses"])


def test_chatbot_status_does_not_expose_api_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    response = client.get("/api/chatbot/status")
    assert response.status_code == 200
    assert response.json() == {
        "status": "configured",
        "provider": "groq",
        "model": "test-model",
        "api_key_configured": True,
    }
    assert "test-secret" not in response.text


def test_chatbot_status_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.get("/api/chatbot/status")
    assert response.status_code == 200
    assert response.json()["status"] == "not_configured"
    assert response.json()["api_key_configured"] is False


def test_chatbot_returns_actionable_error_when_key_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.post(
        "/api/chatbot/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]



def test_inbound_webhook_fails_closed_without_configured_token(monkeypatch):
    monkeypatch.delenv("INBOUND_WEBHOOK_TOKEN", raising=False)
    response = client.post(
        "/api/webhooks/inbound/website",
        json={
            "external_message_id": "test-1",
            "sender_id": "session-1",
            "text": "I want to learn data science",
        },
    )
    assert response.status_code == 503
    assert "INBOUND_WEBHOOK_TOKEN" in response.json()["detail"]


def test_inbound_webhook_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv("INBOUND_WEBHOOK_TOKEN", "test-secret")
    response = client.post(
        "/api/webhooks/inbound/website",
        headers={"Authorization": "Bearer wrong"},
        json={
            "external_message_id": "test-1",
            "sender_id": "session-1",
            "text": "I want to learn data science",
        },
    )
    assert response.status_code == 401


def test_inbound_webhook_requires_verified_external_channel(monkeypatch):
    monkeypatch.setenv("INBOUND_WEBHOOK_TOKEN", "test-secret")
    response = client.post(
        "/api/webhooks/inbound/whatsapp",
        headers={"Authorization": "Bearer test-secret"},
        json={
            "external_message_id": "test-1",
            "sender_id": "sender-1",
            "text": "I want to learn data science",
        },
    )
    assert response.status_code == 400
    assert "verify provider signatures" in response.json()["detail"]
