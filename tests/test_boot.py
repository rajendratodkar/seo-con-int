"""Boot smoke tests: app starts, schema applies, core routes respond.

Run:  pytest tests/ -q   (with the project venv)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


def _client():
    return TestClient(create_app())


def test_health_ok():
    with _client() as client:
        resp = client.get("/api/health/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"


def test_module_families_respond():
    paths = [
        "/api/websites/",
        "/api/references/",
        "/api/research/sources",
        "/api/content-ideas/",
        "/api/discussions/",
        "/api/settings/values",
        "/api/settings/ai-providers",
        "/api/article-plans/",
        "/api/content/drafts",
        "/api/publishing/logs",
        "/api/publishing/config/wordpress",
        "/api/publishing/config/github",
    ]
    with _client() as client:
        for path in paths:
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} -> {resp.status_code}: {resp.text[:200]}"


def test_error_envelope_shape():
    with _client() as client:
        resp = client.get("/api/reports/weekly", params={"website_id": 999999})
        assert resp.status_code == 404
        err = resp.json()["error"]
        assert {"code", "message"} <= set(err)


def test_publishing_rejects_unapproved_draft():
    """Human approval gate: publishing a missing draft returns the error envelope."""
    with _client() as client:
        resp = client.post("/api/publishing/wordpress", json={"draft_id": 999999})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "publish.draft_not_found"
