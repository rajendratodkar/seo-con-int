"""Live-server integration tests.

Run the backend first:
    python scripts/backend/serve.py

Then:
    pytest tests/test_integration_live.py -v --tb=short
"""
import httpx
import pytest

BASE = "http://127.0.0.1:8317"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=15) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Health & System
# ---------------------------------------------------------------------------

class TestHealthSystem:
    def test_health(self, client):
        r = client.get("/api/health/")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"
        assert "version" in body

    def test_diagnostics_info(self, client):
        r = client.get("/api/diagnostics/info")
        assert r.status_code == 200
        body = r.json()
        for key in ("version", "online", "proxy_configured", "sentry_enabled", "log_size_bytes"):
            assert key in body, f"missing key: {key}"

    def test_diagnostics_events_post_and_get(self, client):
        r = client.post("/api/diagnostics/events", json={"event": "action", "detail": "integration_test"})
        assert r.status_code == 200
        r = client.get("/api/diagnostics/events", params={"limit": 10})
        assert r.status_code == 200
        assert r.json()["counts"]["total"] >= 1

    def test_diagnostics_crash(self, client):
        r = client.post("/api/diagnostics/crash", json={
            "message": "test crash",
            "stack": "Traceback...",
            "route": "/test",
        })
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ---------------------------------------------------------------------------
# 2. Websites CRUD
# ---------------------------------------------------------------------------

class TestWebsites:
    def test_list_empty(self, client):
        r = client.get("/api/websites/")
        assert r.status_code == 200
        body = r.json()
        # API returns paginated: {"items": [...], "total": N, "page": 1, "page_size": 50}
        assert "items" in body or isinstance(body, list)

    def test_create(self, client):
        r = client.post("/api/websites/", json={
            "name": "Integration Test Site",
            "url": "https://example-test.com",
        })
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert body["name"] == "Integration Test Site"
        assert "id" in body
        self.__class__._site_id = body["id"]

    def test_get_by_id(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create test did not run")
        r = client.get(f"/api/websites/{site_id}")
        assert r.status_code == 200
        assert r.json()["url"] == "https://example-test.com"

    def test_update(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create test did not run")
        r = client.patch(f"/api/websites/{site_id}", json={"name": "Updated Test Site"})
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Test Site"

    def test_delete(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create test did not run")
        r = client.delete(f"/api/websites/{site_id}")
        assert r.status_code in (200, 204)
        # verify gone
        r = client.get(f"/api/websites/{site_id}")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# 3. References
# ---------------------------------------------------------------------------

class TestReferences:
    def test_list_references(self, client):
        r = client.get("/api/references/")
        assert r.status_code == 200
        refs = r.json()
        assert isinstance(refs, (list, dict)), f"unexpected type: {type(refs)}"

    def test_references_has_seed_data(self, client):
        r = client.get("/api/references/")
        assert r.status_code == 200
        # schema validation confirmed seed data exists
        body = r.json()
        # could be a list or paginated object
        if isinstance(body, list):
            assert len(body) > 0, "no seed references found"
        elif isinstance(body, dict) and "items" in body:
            assert len(body["items"]) > 0


# ---------------------------------------------------------------------------
# 4. Research Sources
# ---------------------------------------------------------------------------

class TestResearchSources:
    def test_list_sources(self, client):
        r = client.get("/api/research/sources")
        assert r.status_code == 200

    def test_create_from_file(self, client):
        content = (
            "Our organic traffic increased by 60% after implementing schema markup. "
            "What are the best practices for product schema? "
            "Internal linking improved our crawl budget significantly."
        )
        r = client.post("/api/research/sources/from-file", json={
            "filename": "integration_notes.txt",
            "content": content,
        })
        assert r.status_code == 200, r.text
        source = r.json()
        assert source["source_type"] == "file"
        assert source["extraction_status"] == "completed"
        assert "id" in source
        self.__class__._source_id = source["id"]

    def test_get_source_detail(self, client):
        source_id = getattr(self.__class__, "_source_id", None)
        if source_id is None:
            pytest.skip("create_from_file did not run")
        r = client.get(f"/api/research/sources/{source_id}")
        assert r.status_code == 200
        detail = r.json()
        assert len(detail["topics"]) > 0
        assert len(detail["claims"]) >= 1
        assert len(detail["questions"]) >= 1

    def test_reject_unsupported_file_type(self, client):
        r = client.post("/api/research/sources/from-file", json={
            "filename": "virus.exe",
            "content": "bad content",
        })
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "research.unsupported_file"


# ---------------------------------------------------------------------------
# 5. Content Ideas
# ---------------------------------------------------------------------------

class TestContentIdeas:
    def test_list_ideas(self, client):
        r = client.get("/api/content-ideas/")
        assert r.status_code == 200

    def test_create_idea(self, client):
        r = client.post("/api/content-ideas/", json={
            "title": "Integration Test Idea",
            "description": "Test idea for E2E validation",
            "source": "manual",
        })
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert body["title"] == "Integration Test Idea"
        self.__class__._idea_id = body["id"]

    def test_get_idea(self, client):
        idea_id = getattr(self.__class__, "_idea_id", None)
        if idea_id is None:
            pytest.skip("create did not run")
        r = client.get(f"/api/content-ideas/{idea_id}")
        assert r.status_code == 200
        assert r.json()["title"] == "Integration Test Idea"

    def test_delete_idea(self, client):
        idea_id = getattr(self.__class__, "_idea_id", None)
        if idea_id is None:
            pytest.skip("create did not run")
        r = client.delete(f"/api/content-ideas/{idea_id}")
        assert r.status_code in (200, 204)


# ---------------------------------------------------------------------------
# 6. Discussions
# ---------------------------------------------------------------------------

class TestDiscussions:
    def test_list_discussions(self, client):
        r = client.get("/api/discussions/")
        assert r.status_code == 200

    def test_create_discussion(self, client):
        r = client.post("/api/discussions/", json={
            "topic": "Integration Test Discussion Topic",
        })
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert body["topic"] == "Integration Test Discussion Topic"
        self.__class__._disc_id = body["id"]

    def test_get_discussion(self, client):
        disc_id = getattr(self.__class__, "_disc_id", None)
        if disc_id is None:
            pytest.skip("create did not run")
        r = client.get(f"/api/discussions/{disc_id}")
        assert r.status_code == 200

    def test_post_message(self, client):
        disc_id = getattr(self.__class__, "_disc_id", None)
        if disc_id is None:
            pytest.skip("create did not run")
        r = client.post(f"/api/discussions/{disc_id}/messages", json={
            "content": "What are the top SEO priorities for this topic?",
            "ask_ai": False,
        })
        assert r.status_code in (200, 201), r.text

    def test_archive_discussion(self, client):
        disc_id = getattr(self.__class__, "_disc_id", None)
        if disc_id is None:
            pytest.skip("create did not run")
        r = client.post(f"/api/discussions/{disc_id}/archive")
        assert r.status_code == 200
        assert r.json()["status"] == "archived"


# ---------------------------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------------------------

class TestSettings:
    def test_get_values(self, client):
        r = client.get("/api/settings/values")
        assert r.status_code == 200

    def test_get_ai_providers(self, client):
        r = client.get("/api/settings/ai-providers")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, (list, dict))

    def test_set_and_get_value(self, client):
        r = client.put("/api/settings/values/test.integration.flag", json={
            "value": "true",
        })
        assert r.status_code == 200, r.text
        # verify it was set
        r = client.get("/api/settings/values/test.integration.flag")
        assert r.status_code == 200
        assert r.json()["value"] == "true"


# ---------------------------------------------------------------------------
# 8. Article Plans
# ---------------------------------------------------------------------------

class TestArticlePlans:
    def test_list_plans(self, client):
        r = client.get("/api/article-plans/")
        assert r.status_code == 200

    def test_create_plan(self, client):
        r = client.post("/api/article-plans/", json={
            "title": "Integration Test Plan",
            "topic": "SEO best practices",
        })
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert body["title"] == "Integration Test Plan"
        self.__class__._plan_id = body["id"]

    def test_get_plan(self, client):
        plan_id = getattr(self.__class__, "_plan_id", None)
        if plan_id is None:
            pytest.skip("create did not run")
        r = client.get(f"/api/article-plans/{plan_id}")
        assert r.status_code == 200

    def test_delete_plan(self, client):
        plan_id = getattr(self.__class__, "_plan_id", None)
        if plan_id is None:
            pytest.skip("create did not run")
        r = client.delete(f"/api/article-plans/{plan_id}")
        assert r.status_code in (200, 204)


# ---------------------------------------------------------------------------
# 9. Content Drafts
# ---------------------------------------------------------------------------

class TestContentDrafts:
    def test_list_drafts(self, client):
        r = client.get("/api/content/drafts")
        assert r.status_code == 200

    def test_list_drafts(self, client):
        r = client.get("/api/content/drafts")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body or isinstance(body, list)

    def test_generate_draft_requires_plan(self, client):
        """Drafts are generated from plans, not created directly."""
        r = client.post("/api/content/drafts/generate", json={"plan_id": 999999})
        assert r.status_code == 404

    def test_draft_not_found(self, client):
        r = client.get("/api/content/drafts/999999")
        assert r.status_code == 404
        assert "error" in r.json()


# ---------------------------------------------------------------------------
# 10. Publishing
# ---------------------------------------------------------------------------

class TestPublishing:
    def test_publish_logs(self, client):
        r = client.get("/api/publishing/logs")
        assert r.status_code == 200

    def test_wordpress_config(self, client):
        r = client.get("/api/publishing/config/wordpress")
        assert r.status_code == 200

    def test_github_config(self, client):
        r = client.get("/api/publishing/config/github")
        assert r.status_code == 200

    def test_reject_unapproved_draft(self, client):
        r = client.post("/api/publishing/wordpress", json={"draft_id": 999999})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "publish.draft_not_found"


# ---------------------------------------------------------------------------
# 11. Google Analytics
# ---------------------------------------------------------------------------

class TestGoogleAnalytics:
    def test_connection_not_found(self, client):
        r = client.get("/api/google-analytics/connection", params={"website_id": 999999})
        assert r.status_code == 200
        assert r.json()["connection"] is None

    def test_summary_not_found(self, client):
        r = client.get("/api/google-analytics/summary", params={"website_id": 999999})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "ga.connection_not_found"


# ---------------------------------------------------------------------------
# 12. SEO Findings & Opportunities
# ---------------------------------------------------------------------------

class TestSEOModules:
    def test_findings_list(self, client):
        r = client.get("/api/findings/", params={"website_id": 1})
        assert r.status_code == 200

    def test_opportunities_list(self, client):
        r = client.get("/api/opportunities/", params={"website_id": 1})
        assert r.status_code == 200

    def test_topic_clusters_list(self, client):
        r = client.get("/api/topic-clusters/", params={"website_id": 1})
        assert r.status_code == 200

    def test_internal_links_list(self, client):
        r = client.get("/api/internal-links/", params={"website_id": 1})
        assert r.status_code == 200

    def test_content_audit_list(self, client):
        r = client.get("/api/content-audit/", params={"website_id": 1})
        assert r.status_code == 200

    def test_keywords_list(self, client):
        r = client.get("/api/keywords/", params={"website_id": 1})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 13. Error Envelope Consistency
# ---------------------------------------------------------------------------

class TestErrorEnvelopes:
    def test_not_found_returns_envelope(self, client):
        r = client.get("/api/websites/999999")
        assert r.status_code == 404
        body = r.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_invalid_json_rejected(self, client):
        r = client.post("/api/websites/", content="not json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_missing_required_fields(self, client):
        r = client.post("/api/websites/", json={})
        assert r.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 14. Markdown Engine (deterministic, no network)
# ---------------------------------------------------------------------------

class TestMarkdownEngine:
    def test_to_html_headings(self, client):
        """Markdown engine is local — just verify import works via API or direct."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
        from app.engines.content.markdown import to_html
        out = to_html("# Hello\n\nWorld")
        assert "<h1>Hello</h1>" in out
        assert "<p>World</p>" in out

    def test_to_html_code_block(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
        from app.engines.content.markdown import to_html
        out = to_html("```\ncode here\n```")
        assert "<pre><code>" in out
