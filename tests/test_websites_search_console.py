"""Integration tests for website detect/crawl and Search Console OAuth flow.

Covers:
  - Website CRUD + detect + test + crawl job lifecycle
  - Platform detection heuristics (WordPress, Astro, unknown)
  - Sitemap auto-discovery
  - Search Console OAuth consent URL + state validation
  - Search Console manual import
  - Search Console properties + stats

Live-server tests need the backend running:
    python scripts/backend/serve.py

Mocked-network tests run against an in-process app with a temp database,
so no backend is required for those.

Then:
    pytest tests/test_websites_search_console.py -v --tb=short
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import settings
from app.database import connection
from app.integrations.crawler.parser import parse_html
from app.integrations.crawler.robots import RobotsPolicy
from app.modules.websites.detectors import detect_platform_from_html

BASE = "http://127.0.0.1:8317"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=15) as c:
        yield c


@pytest.fixture(scope="module")
def app_client():
    """In-process app on a temp database so unittest.mock patches take effect.

    The live-server client above runs requests in a separate process, where
    patch() cannot intercept HTTP calls.
    """
    original_db = settings.database_path
    tmp = Path(tempfile.mkdtemp(prefix="sci-test-")) / "test.db"
    settings.database_path = tmp
    connection._engine = None
    connection._SessionFactory = None
    try:
        with TestClient(create_app()) as c:
            yield c
    finally:
        connection._engine = None
        connection._SessionFactory = None
        settings.database_path = original_db


# ---------------------------------------------------------------------------
# 1. Platform Detection Heuristics (unit — no network)
# ---------------------------------------------------------------------------

class TestPlatformDetection:
    """Test the detect_platform_from_html function with various HTML signatures."""

    def test_wordpress_via_wp_content(self):
        html = '<html><head></head><body><link href="/wp-content/themes/style.css"></body></html>'
        assert detect_platform_from_html(html, {}) == "wordpress"

    def test_wordpress_via_wp_includes(self):
        html = '<script src="/wp-includes/js/jquery.min.js"></script>'
        assert detect_platform_from_html(html, {}) == "wordpress"

    def test_wordpress_via_generator_meta(self):
        html = '<meta name="generator" content="WordPress 6.5">'
        assert detect_platform_from_html(html, {}) == "wordpress"

    def test_wordpress_via_wp_json(self):
        html = '<link rel="https://api.w.org/" href="/wp-json/wp/v2/posts">'
        assert detect_platform_from_html(html, {}) == "wordpress"

    def test_wordpress_via_header(self):
        html = "<html><body>normal</body></html>"
        headers = {"x-powered-by": "WP Engine"}
        assert detect_platform_from_html(html, headers) == "wordpress"

    def test_astro_via_generator(self):
        html = '<meta name="generator" content="Astro v4.0">'
        assert detect_platform_from_html(html, {}) == "astro"

    def test_astro_via_islands(self):
        html = '<script type="module">import "astro/islands"</script>'
        assert detect_platform_from_html(html, {}) == "astro"

    def test_astro_via_dunder(self):
        html = '<script>import "__astro"</script>'
        assert detect_platform_from_html(html, {}) == "astro"

    def test_static_via_nextjs_generator(self):
        html = '<meta name="generator" content="Next.js">'
        assert detect_platform_from_html(html, {}) == "static"

    def test_unknown_for_plain_html(self):
        html = "<html><head><title>Plain</title></head><body>Hello</body></html>"
        assert detect_platform_from_html(html, {}) == "unknown"

    def test_empty_html(self):
        assert detect_platform_from_html("", {}) == "unknown"

    def test_case_insensitive(self):
        html = '<META NAME="GENERATOR" CONTENT="wordpress">'
        assert detect_platform_from_html(html, {}) == "wordpress"


# ---------------------------------------------------------------------------
# 2. HTML Parser — Crawl Data Extraction
# ---------------------------------------------------------------------------

class TestCrawlDataExtraction:
    """Verify parse_html extracts all fields the crawler records."""

    def test_full_page_extraction(self):
        html = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <title>SEO Best Practices Guide</title>
            <meta name="description" content="A comprehensive guide to SEO">
            <link rel="canonical" href="https://example.com/seo-guide">
            <meta property="article:published_time" content="2026-01-10T08:00:00Z">
            <meta property="article:modified_time" content="2026-06-15T12:00:00Z">
            <script type="application/ld+json">{"@type":"Article","headline":"SEO Guide"}</script>
        </head>
        <body>
            <h1>SEO Best Practices</h1>
            <h2>Technical SEO</h2>
            <p>Learn about technical SEO fundamentals.</p>
            <a href="/about">About Us</a>
            <a href="https://example.com/tools" rel="nofollow">SEO Tools</a>
            <a href="https://external.com/link">External Link</a>
            <img src="/images/seo-diagram.png" alt="SEO diagram">
            <img src="/images/chart.jpg">
        </body>
        </html>"""
        page = parse_html("https://example.com/seo-guide", html, 200)

        assert page.title == "SEO Best Practices Guide"
        assert page.meta_description == "A comprehensive guide to SEO"
        assert page.canonical == "https://example.com/seo-guide"
        assert page.published_at == "2026-01-10T08:00:00Z"
        assert page.modified_at == "2026-06-15T12:00:00Z"
        assert len(page.schema_json) == 1
        assert page.schema_json[0]["@type"] == "Article"

        # Headings
        assert len(page.headings) == 2
        assert page.headings[0] == {"level": 1, "text": "SEO Best Practices"}
        assert page.headings[1] == {"level": 2, "text": "Technical SEO"}

        # Links (http/https only, deduplicated)
        assert len(page.links) == 3
        nofollow_links = [l for l in page.links if l["is_nofollow"]]
        assert len(nofollow_links) == 1
        assert nofollow_links[0]["anchor_text"] == "SEO Tools"

        # Images
        assert len(page.images) == 2
        assert page.images[0]["alt"] == "SEO diagram"
        assert page.images[1]["alt"] == ""

        # Word count
        assert page.word_count > 0

    def test_page_with_no_headings(self):
        html = "<html><body><p>Just a paragraph.</p></body></html>"
        page = parse_html("https://example.com/", html, 200)
        assert page.headings == []
        assert page.word_count >= 3

    def test_page_with_many_heading_levels(self):
        html = ""
        for i in range(1, 7):
            html += f"<h{i}>Level {i}</h" + str(i) + ">"
        page = parse_html("https://example.com/", html, 200)
        assert len(page.headings) == 6
        assert [h["level"] for h in page.headings] == [1, 2, 3, 4, 5, 6]


# ---------------------------------------------------------------------------
# 3. Website CRUD via Live Server
# ---------------------------------------------------------------------------

class TestWebsiteCRUD:
    """Full CRUD cycle against the live server."""

    def test_create_website(self, client):
        r = client.post("/api/websites/", json={
            "name": "Test Crawl Site",
            "url": "https://example-test-crawl.com",
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Test Crawl Site"
        assert body["url"] == "https://example-test-crawl.com"
        assert body["platform"] == "unknown"
        self.__class__._site_id = body["id"]

    def test_get_website(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create did not run")
        r = client.get(f"/api/websites/{site_id}")
        assert r.status_code == 200
        assert r.json()["id"] == site_id

    def test_update_website(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create did not run")
        r = client.patch(f"/api/websites/{site_id}", json={
            "name": "Updated Crawl Site",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Crawl Site"

    def test_list_websites_includes_new(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create did not run")
        r = client.get("/api/websites/")
        assert r.status_code == 200
        body = r.json()
        items = body.get("items", body) if isinstance(body, dict) else body
        ids = [s["id"] for s in items]
        assert site_id in ids

    def test_delete_website(self, client):
        site_id = getattr(self.__class__, "_site_id", None)
        if site_id is None:
            pytest.skip("create did not run")
        r = client.delete(f"/api/websites/{site_id}")
        assert r.status_code == 204
        # verify gone
        r = client.get(f"/api/websites/{site_id}")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# 4. Website Detect Endpoint (mocked network)
# ---------------------------------------------------------------------------

class TestWebsiteDetect:
    """Test the /detect endpoint with mocked HTTP responses (in-process app)."""

    def _create_site(self, client):
        r = client.post("/api/websites/", json={
            "name": "Detect Test",
            "url": "https://wordpress-example.com",
        })
        assert r.status_code == 201
        return r.json()["id"]

    def test_detect_wordpress_site(self, app_client):
        site_id = self._create_site(app_client)
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '<html><link href="/wp-content/themes/style.css"></html>'
            mock_response.headers = {"x-powered-by": "PHP"}

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            with patch("app.modules.websites.detectors.http_client", return_value=mock_client):
                r = app_client.post(f"/api/websites/{site_id}/detect")

            assert r.status_code == 200
            body = r.json()
            assert body["platform"] == "wordpress"
            assert body["reachable"] is True
            assert body["status_code"] == 200
        finally:
            app_client.delete(f"/api/websites/{site_id}")

    def test_detect_unreachable_site(self, app_client):
        site_id = self._create_site(app_client)
        try:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            with patch("app.modules.websites.detectors.http_client", return_value=mock_client):
                r = app_client.post(f"/api/websites/{site_id}/detect")

            assert r.status_code == 200
            body = r.json()
            assert body["reachable"] is False
            assert body["status_code"] is None
        finally:
            app_client.delete(f"/api/websites/{site_id}")

    def test_detect_updates_platform_in_db(self, app_client):
        site_id = self._create_site(app_client)
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '<meta name="generator" content="Astro v4">'
            mock_response.headers = {}

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            with patch("app.modules.websites.detectors.http_client", return_value=mock_client):
                app_client.post(f"/api/websites/{site_id}/detect")

            # Verify platform was persisted
            r = app_client.get(f"/api/websites/{site_id}")
            assert r.json()["platform"] == "astro"
        finally:
            app_client.delete(f"/api/websites/{site_id}")


# ---------------------------------------------------------------------------
# 5. Website Test Connectivity Endpoint
# ---------------------------------------------------------------------------

class TestWebsiteTestConnectivity:
    """Test the /test endpoint (in-process app, mocked HTTP)."""

    def _create_site(self, client):
        r = client.post("/api/websites/", json={
            "name": "Connectivity Test",
            "url": "https://connectivity-test.com",
        })
        return r.json()["id"]

    def test_test_reachable(self, app_client):
        site_id = self._create_site(app_client)
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            with patch("app.modules.websites.detectors.http_client", return_value=mock_client):
                r = app_client.post(f"/api/websites/{site_id}/test")

            assert r.status_code == 200
            body = r.json()
            assert body["reachable"] is True
            assert body["status_code"] == 200
        finally:
            app_client.delete(f"/api/websites/{site_id}")

    def test_test_unreachable(self, app_client):
        site_id = self._create_site(app_client)
        try:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            with patch("app.modules.websites.detectors.http_client", return_value=mock_client):
                r = app_client.post(f"/api/websites/{site_id}/test")

            assert r.status_code == 200
            body = r.json()
            assert body["reachable"] is False
            assert body["status_code"] is None
        finally:
            app_client.delete(f"/api/websites/{site_id}")


# ---------------------------------------------------------------------------
# 6. Crawl Job Lifecycle
# ---------------------------------------------------------------------------

class TestCrawlJobLifecycle:
    """Test crawl start + status endpoints."""

    def _create_site(self, client):
        r = client.post("/api/websites/", json={
            "name": "Crawl Job Test",
            "url": "https://crawl-job-test.com",
        })
        return r.json()["id"]

    def test_start_crawl_returns_job(self, client):
        site_id = self._create_site(client)
        try:
            r = client.post(f"/api/websites/{site_id}/crawl/start", params={"max_pages": 5})
            assert r.status_code == 202, r.text
            body = r.json()
            assert "job_id" in body
            assert body["status"] == "running"
            self.__class__._job_id = body["job_id"]
        finally:
            client.delete(f"/api/websites/{site_id}")

    def test_crawl_status_returns_job_info(self, client):
        job_id = getattr(self.__class__, "_job_id", None)
        if job_id is None:
            pytest.skip("start_crawl did not run")
        r = client.get(f"/api/websites/crawl/{job_id}/status")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == job_id
        assert body["sync_type"] == "crawl"
        assert body["status"] in ("running", "completed", "failed")

    def test_crawl_status_nonexistent_job(self, client):
        r = client.get("/api/websites/crawl/999999/status")
        assert r.status_code == 404

    def test_start_crawl_with_max_pages_limit(self, client):
        site_id = self._create_site(client)
        try:
            r = client.post(f"/api/websites/{site_id}/crawl/start", params={"max_pages": 1})
            assert r.status_code == 202
        finally:
            client.delete(f"/api/websites/{site_id}")


# ---------------------------------------------------------------------------
# 7. Sitemap Auto-Discovery (mocked)
# ---------------------------------------------------------------------------

class TestSitemapDiscovery:
    """Test the sitemap detection from the detect endpoint."""

    def test_detect_finds_sitemap(self, app_client):
        r = app_client.post("/api/websites/", json={
            "name": "Sitemap Test",
            "url": "https://sitemap-test.com",
        })
        site_id = r.json()["id"]
        try:
            # Mock: homepage returns 200, /sitemap.xml returns valid XML
            homepage = MagicMock(status_code=200, text="<html><body>Hi</body></html>", headers={})
            sitemap = MagicMock(
                status_code=200,
                text='<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://sitemap-test.com/</loc></url></urlset>',
                headers={},
            )

            call_count = 0

            async def mock_get(url, **kw):
                nonlocal call_count
                call_count += 1
                if "sitemap" in url:
                    return sitemap
                return homepage

            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            with patch("app.modules.websites.detectors.http_client", return_value=mock_client):
                r = app_client.post(f"/api/websites/{site_id}/detect")

            assert r.status_code == 200
            body = r.json()
            assert body["sitemap_url"] is not None
            assert "sitemap" in body["sitemap_url"]
        finally:
            app_client.delete(f"/api/websites/{site_id}")


# ---------------------------------------------------------------------------
# 8. Search Console OAuth Flow
# ---------------------------------------------------------------------------

class TestSearchConsoleOAuth:
    """Test the OAuth consent URL and callback state validation."""

    def test_oauth_url_returns_configured_flag(self, client):
        r = client.get("/api/search-console/oauth/url")
        assert r.status_code == 200
        body = r.json()
        assert "url" in body
        assert "configured" in body
        assert isinstance(body["configured"], bool)

    def test_oauth_url_when_not_configured(self, app_client):
        """Without Google credentials, configured should be False."""
        r = app_client.get("/api/search-console/oauth/url")
        assert r.status_code == 200
        body = r.json()
        # In-process app has no Google OAuth credentials
        assert body["configured"] is False

    def test_oauth_callback_rejects_bad_state(self, client):
        """Callback with wrong state must fail."""
        r = client.get("/api/search-console/oauth/callback", params={
            "code": "fake_code",
            "state": "wrong_state_value",
        })
        assert r.status_code == 400
        body = r.json()
        assert body["error"]["code"] == "search_console.bad_state"

    def test_oauth_callback_rejects_empty_state(self, client):
        r = client.get("/api/search-console/oauth/callback", params={
            "code": "fake_code",
            "state": "",
        })
        assert r.status_code == 400

    def test_search_console_not_connected_blocks_discover(self, client):
        """discover_properties requires a valid access token."""
        r = client.get("/api/search-console/properties/discover")
        # Should fail because no OAuth token is stored
        assert r.status_code in (400, 502)


# ---------------------------------------------------------------------------
# 9. Search Console Manual Import
# ---------------------------------------------------------------------------

class TestSearchConsoleManualImport:
    """Test the manual CSV import endpoint (no OAuth required)."""

    def test_manual_import_rows(self, client):
        # Create a real website so the property FK has a valid target.
        site = client.post("/api/websites/", json={
            "name": "Manual Import Test",
            "url": "https://manual-import-test.com",
        })
        website_id = site.json()["id"]
        try:
            r = client.post("/api/search-console/import/manual", json={
                "website_id": website_id,
                "site_url": "https://manual-import-test.com",
                "rows": [
                    {
                        "date": "2026-08-01",
                        "query": "seo tips",
                        "page_url": "https://manual-import-test.com/seo",
                        "clicks": 50,
                        "impressions": 3000,
                        "ctr": 0.0167,
                        "position": 5.5,
                    },
                    {
                        "date": "2026-08-02",
                        "query": "content strategy",
                        "page_url": "https://manual-import-test.com/content",
                        "clicks": 25,
                        "impressions": 1500,
                        "ctr": 0.0167,
                        "position": 8.2,
                    },
                ],
            })
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["imported"] >= 2
            assert "property_id" in body
        finally:
            client.delete(f"/api/websites/{website_id}")

    def test_manual_import_empty_rows(self, client):
        site = client.post("/api/websites/", json={
            "name": "Empty Import Test",
            "url": "https://empty-import-test.com",
        })
        website_id = site.json()["id"]
        try:
            r = client.post("/api/search-console/import/manual", json={
                "website_id": website_id,
                "site_url": "https://empty-import-test.com",
                "rows": [],
            })
            assert r.status_code == 200
            body = r.json()
            assert body["imported"] == 0
        finally:
            client.delete(f"/api/websites/{website_id}")


# ---------------------------------------------------------------------------
# 10. Search Console Properties & Stats
# ---------------------------------------------------------------------------

class TestSearchConsolePropertiesStats:
    """Test the properties and stats endpoints."""

    def test_list_properties(self, client):
        r = client.get("/api/search-console/properties")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)

    def test_stats_endpoint(self, client):
        r = client.get("/api/search-console/stats")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)

    def test_queries_endpoint_requires_website_id(self, client):
        r = client.get("/api/search-console/queries")
        assert r.status_code == 422  # missing required query param

    def test_pages_endpoint_requires_website_id(self, client):
        r = client.get("/api/search-console/pages")
        assert r.status_code == 422

    def test_compare_endpoint_requires_params(self, client):
        r = client.get("/api/search-console/compare")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# 11. Error Envelopes for Websites + Search Console
# ---------------------------------------------------------------------------

class TestErrorEnvelopes:
    """Verify proper error shapes for edge cases."""

    def test_get_nonexistent_website(self, client):
        r = client.get("/api/websites/999999")
        assert r.status_code == 404
        body = r.json()
        assert body["error"]["code"] == "website.not_found"

    def test_detect_nonexistent_website(self, client):
        r = client.post("/api/websites/999999/detect")
        assert r.status_code == 404

    def test_crawl_nonexistent_website(self, client):
        r = client.post("/api/websites/999999/crawl/start")
        assert r.status_code == 404

    def test_duplicate_website_rejected(self, client):
        """Creating two websites with the same URL should fail."""
        r1 = client.post("/api/websites/", json={
            "name": "Dup Test 1",
            "url": "https://dup-test-same-url.com",
        })
        assert r1.status_code == 201
        site_id = r1.json()["id"]
        try:
            r2 = client.post("/api/websites/", json={
                "name": "Dup Test 2",
                "url": "https://dup-test-same-url.com",
            })
            assert r2.status_code == 409
            assert r2.json()["error"]["code"] == "website.duplicate"
        finally:
            client.delete(f"/api/websites/{site_id}")

    def test_create_website_missing_name(self, client):
        r = client.post("/api/websites/", json={"url": "https://no-name.com"})
        assert r.status_code == 422

    def test_create_website_missing_url(self, client):
        r = client.post("/api/websites/", json={"name": "No URL"})
        assert r.status_code == 422

    def test_connect_property_not_found(self, client):
        r = client.post("/api/search-console/properties/999999/connect", params={"website_id": 1})
        assert r.status_code == 404
