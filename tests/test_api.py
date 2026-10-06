"""API contract tests using FastAPI's TestClient (requires httpx)."""
import importlib.util

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("fastapi.testclient") is None
    or importlib.util.find_spec("httpx") is None,
    reason="fastapi testclient / httpx not installed",
)


def _client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_health():
    c = _client()
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_full_flow():
    c = _client()
    r = c.post("/api/analysis", json={"demo_mode": True})
    assert r.status_code == 202
    run_id = r.json()["run_id"]

    detail = c.get(f"/api/analysis/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"

    assert c.get(f"/api/flood-zones/{run_id}").status_code == 200
    assert c.get(f"/api/infrastructure/{run_id}").status_code == 200
    assert c.get(f"/api/connectivity/{run_id}").status_code == 200

    q = c.post(
        "/api/agent/query",
        json={"run_id": run_id, "question": "Which settlements are cut off?"},
    )
    assert q.status_code == 200
    assert q.json()["grounded"] is True

    rep = c.get(f"/api/agent/report/{run_id}")
    assert rep.status_code == 200
    assert "body_md" in rep.json()
