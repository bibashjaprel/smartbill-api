from fastapi.testclient import TestClient

import app.core.database as database_module
import app.main as main_module


class _FakeSession:
    def close(self) -> None:
        return None


def test_root_response_includes_request_id_header():
    client = TestClient(main_module.app)

    response = client.get("/", headers={"X-Request-Id": "req-test-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-test-123"
    assert response.json()["meta"]["request_id"] == "req-test-123"


def test_ready_returns_success_when_database_is_healthy(monkeypatch):
    monkeypatch.setattr(database_module, "SessionLocal", lambda: _FakeSession())
    monkeypatch.setattr(main_module, "check_database_readiness", lambda db: True)

    client = TestClient(main_module.app)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["data"]["ready"] is True
    assert response.json()["meta"]["request_id"]


def test_ready_returns_error_when_database_check_fails(monkeypatch):
    monkeypatch.setattr(database_module, "SessionLocal", lambda: _FakeSession())

    def _raise_error(_db):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main_module, "check_database_readiness", _raise_error)

    client = TestClient(main_module.app)
    response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "READINESS_ERROR"
    assert body["error"]["request_id"]
