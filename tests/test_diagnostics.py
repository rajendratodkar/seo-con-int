"""Diagnostics (analytics/crash/info), file-based research sources, proxy support."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


def _client():
    return TestClient(create_app())


def test_usage_events_roundtrip():
    with _client() as client:
        resp = client.post("/api/diagnostics/events", json={"event": "action", "detail": "unit_test"})
        assert resp.status_code == 200
        resp = client.get("/api/diagnostics/events", params={"limit": 50})
        assert resp.status_code == 200
        body = resp.json()
        assert body["counts"]["total"] >= 1
        assert any(e["detail"] == "unit_test" for e in body["items"])


def test_invalid_event_kind_rejected():
    with _client() as client:
        resp = client.post("/api/diagnostics/events", json={"event": "bogus"})
        assert resp.status_code == 422  # pydantic pattern guard


def test_crash_endpoint_records():
    with _client() as client:
        resp = client.post(
            "/api/diagnostics/crash",
            json={"message": "unit test crash", "stack": "trace...", "route": "/"},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


def test_info_reports_system_state():
    with _client() as client:
        resp = client.get("/api/diagnostics/info")
        assert resp.status_code == 200
        body = resp.json()
        assert {"version", "online", "proxy_configured", "sentry_enabled", "log_size_bytes"} <= set(body)


def test_research_from_file_extracts_locally():
    content = (
        "Organic traffic grew 45% in three months after fixing internal links. "
        "How do you improve internal linking without creating orphan pages? "
        "Our crawl budget doubled when we removed thin pages from the sitemap."
    )
    with _client() as client:
        resp = client.post(
            "/api/research/sources/from-file",
            json={"filename": "notes.txt", "content": content},
        )
        assert resp.status_code == 200, resp.text
        source = resp.json()
        assert source["source_type"] == "file"
        assert source["availability_status"] == "full"
        assert source["extraction_status"] == "completed"

        detail = client.get(f"/api/research/sources/{source['id']}").json()
        assert len(detail["topics"]) > 0
        assert len(detail["claims"]) >= 1  # the 45% sentence
        assert any("internal linking" in q["question"].lower() for q in detail["questions"])


def test_research_from_file_rejects_unsupported_type():
    with _client() as client:
        resp = client.post(
            "/api/research/sources/from-file",
            json={"filename": "malware.exe", "content": "x"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "research.unsupported_file"


def test_http_client_honors_proxy(monkeypatch):
    from app.core import http as core_http

    monkeypatch.setattr(core_http.settings, "http_proxy", "http://proxy.local:3128")
    client = core_http.http_client()
    assert len(client._mounts) > 0  # proxy transport mounted
    monkeypatch.setattr(core_http.settings, "http_proxy", "")
    client = core_http.http_client()
    assert len(client._mounts) == 0
