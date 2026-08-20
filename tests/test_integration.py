"""Integration tests — exercises full request cycle with TestClient + real DB.

Run:  cd backend && python -m pytest ../tests/test_integration.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import create_app  # noqa: E402


def _client():
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Health & infrastructure
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_endpoint(self):
        with _client() as c:
            r = c.get("/api/health/")
            assert r.status_code == 200
            assert r.json()["database"] == "ok"

    def test_error_envelope_shape(self):
        with _client() as c:
            r = c.get("/api/websites/999999")
            assert r.status_code in (404, 405)
            body = r.json()
            if "error" in body:
                assert {"code", "message"} <= set(body["error"])


# ---------------------------------------------------------------------------
# Websites CRUD
# ---------------------------------------------------------------------------

class TestWebsitesCRUD:
    def test_create_and_list_and_delete(self):
        with _client() as c:
            # Create
            r = c.post("/api/websites/", json={"name": "Integration Test", "url": "https://inttest.example.com"})
            assert r.status_code in (200, 201), r.text
            site = r.json()
            assert site["name"] == "Integration Test"
            site_id = site["id"]

            # List — our new site should appear
            r = c.get("/api/websites/")
            assert r.status_code == 200
            body = r.json()
            items = body.get("items", body)
            ids = [s["id"] for s in items]
            assert site_id in ids

            # Delete
            r = c.delete(f"/api/websites/{site_id}")
            assert r.status_code in (200, 204)


# ---------------------------------------------------------------------------
# Research → Idea → Plan workflow
# ---------------------------------------------------------------------------

class TestResearchToPlanWorkflow:
    """Test the full content pipeline: research → idea → plan."""

    _source_id = None
    _idea_id = None
    _plan_id = None

    def test_01_upload_research(self):
        with _client() as c:
            r = c.post("/api/research/sources/from-file", json={
                "filename": "test-notes.txt",
                "content": (
                    "SEO best practices for 2026. Core Web Vitals are critical. "
                    "Internal linking improves crawlability. Schema markup boosts "
                    "rich snippets. Question: How to balance SEO with UX?"
                ),
            })
            assert r.status_code == 200, r.text
            source = r.json()
            assert source["source_type"] == "file"
            TestResearchToPlanWorkflow._source_id = source["id"]

    def test_02_source_has_topics(self):
        sid = TestResearchToPlanWorkflow._source_id
        if sid is None:
            return
        with _client() as c:
            r = c.get(f"/api/research/sources/{sid}")
            assert r.status_code == 200
            detail = r.json()
            assert len(detail.get("topics", [])) >= 1

    def test_03_create_idea(self):
        import time
        with _client() as c:
            r = c.post("/api/content-ideas/", json={
                "title": f"SEO Guide Integration {int(time.time())}",
                "description": "Comprehensive guide based on research",
                "website_id": None,
            })
            assert r.status_code in (200, 201), r.text
            idea = r.json()
            assert idea["status"] == "draft"
            TestResearchToPlanWorkflow._idea_id = idea["id"]

    def test_04_approve_idea(self):
        iid = TestResearchToPlanWorkflow._idea_id
        if iid is None:
            return
        with _client() as c:
            r = c.patch(f"/api/content-ideas/{iid}/status", json={"status": "approved"})
            assert r.status_code == 200
            assert r.json()["status"] == "approved"

    def test_05_create_plan_from_idea(self):
        iid = TestResearchToPlanWorkflow._idea_id
        if iid is None:
            return
        with _client() as c:
            r = c.post("/api/article-plans/from-idea", json={"idea_id": iid, "website_id": None})
            assert r.status_code in (200, 201), r.text
            plan = r.json()
            assert "SEO Guide" in plan["title"]
            TestResearchToPlanWorkflow._plan_id = plan["id"]

    def test_06_plan_list_includes_new(self):
        pid = TestResearchToPlanWorkflow._plan_id
        if pid is None:
            return
        with _client() as c:
            r = c.get("/api/article-plans/")
            assert r.status_code == 200
            body = r.json()
            items = body.get("items", body)
            ids = [p["id"] for p in items]
            assert pid in ids


# ---------------------------------------------------------------------------
# Content Refresh Scheduler
# ---------------------------------------------------------------------------

class TestContentRefresh:
    def _create_test_site(self, c):
        r = c.post("/api/websites/", json={"name": "Refresh Test", "url": "https://refresh.example.com"})
        return r.json()["id"]

    def test_stats_empty(self):
        with _client() as c:
            site_id = self._create_test_site(c)
            r = c.get("/api/content-refresh/stats", params={"website_id": site_id})
            assert r.status_code == 200
            stats = r.json()
            assert stats["total_schedules"] == 0
            c.delete(f"/api/websites/{site_id}")

    def test_rules_crud(self):
        with _client() as c:
            site_id = self._create_test_site(c)
            # Create rule
            r = c.post("/api/content-refresh/rules", json={
                "website_id": site_id, "name": "Test Rule",
                "min_age_days": 60, "traffic_drop_pct": 15.0,
            })
            assert r.status_code in (200, 201), r.text
            rule = r.json()
            rule_id = rule["id"]
            assert rule["name"] == "Test Rule"

            # List rules
            r = c.get("/api/content-refresh/rules", params={"website_id": site_id})
            assert r.status_code == 200
            assert len(r.json()) >= 1

            # Delete rule
            r = c.delete(f"/api/content-refresh/rules/{rule_id}")
            assert r.status_code == 200
            c.delete(f"/api/websites/{site_id}")


# ---------------------------------------------------------------------------
# SEO Checklist
# ---------------------------------------------------------------------------

class TestSEOChecklist:
    def test_list_endpoint(self):
        with _client() as c:
            r = c.get("/api/seo-checklist", params={"website_id": 1})
            assert r.status_code == 200


# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------

class TestMonitoring:
    def test_channels_list(self):
        with _client() as c:
            r = c.get("/api/monitoring/channels")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_rules_list(self):
        with _client() as c:
            r = c.get("/api/monitoring/rules")
            assert r.status_code == 200
            assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Redirects
# ---------------------------------------------------------------------------

class TestRedirects:
    def test_stats_empty(self):
        with _client() as c:
            r = c.get("/api/redirects/stats", params={"website_id": 1})
            assert r.status_code == 200
            stats = r.json()
            assert "total" in stats


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

class TestDiagnostics:
    def test_info(self):
        with _client() as c:
            r = c.get("/api/diagnostics/info")
            assert r.status_code == 200
            info = r.json()
            assert "app" in info
            assert "version" in info

    def test_track_event(self):
        with _client() as c:
            r = c.get("/api/diagnostics/events")
            assert r.status_code == 200
