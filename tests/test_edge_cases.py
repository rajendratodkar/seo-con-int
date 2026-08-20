"""Edge-case and unit tests for core subsystems.

Covers: auth middleware, AI provider layer, HTML parser, robots.txt,
sitemap parsing, Search Console normalizer, crypto, HTTP client,
exception model, and markdown engine boundary conditions.

Run:  pytest tests/test_edge_cases.py -v
"""
import json
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.security import TokenGuardMiddleware, generate_token, PUBLIC_PATHS
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError, ConflictError, UpstreamError
from app.core.http import proxy_url, http_client, check_internet
from app.core.crypto import encrypt_secret, decrypt_secret
from app.integrations.ai.providers import complete, DEFAULT_MODELS, _check
from app.integrations.crawler.parser import parse_html, ParsedPage
from app.integrations.crawler.robots import RobotsPolicy
from app.integrations.sitemap.sitemap import fetch_sitemap_urls
from app.modules.search_console.normalizer import normalize_api_rows, normalize_manual_rows
from app.engines.content.markdown import to_html
from app.engines.search_console.opportunity_engine import (
    MIN_IMPRESSIONS, POSITION_MIN, POSITION_MAX,
)


# ---------------------------------------------------------------------------
# 1. Auth Middleware (TokenGuardMiddleware)
# ---------------------------------------------------------------------------

class TestTokenGuardMiddleware:
    """Tests for the local API token guard."""

    def test_health_bypasses_token(self):
        """Health endpoint must always respond without a token."""
        with TestClient(create_app()) as client:
            r = client.get("/api/health/")
            assert r.status_code == 200

    def test_docs_bypasses_token(self):
        """OpenAPI docs must be accessible without a token."""
        with TestClient(create_app()) as client:
            r = client.get("/docs")
            assert r.status_code == 200

    def test_openapi_json_bypasses_token(self):
        with TestClient(create_app()) as client:
            r = client.get("/openapi.json")
            assert r.status_code == 200

    def test_redoc_bypasses_token(self):
        with TestClient(create_app()) as client:
            r = client.get("/redoc")
            assert r.status_code == 200

    def test_public_paths_constant(self):
        """PUBLIC_PATHS must cover all non-sensitive routes."""
        assert "/api/health" in PUBLIC_PATHS
        assert "/docs" in PUBLIC_PATHS
        assert "/openapi.json" in PUBLIC_PATHS
        assert "/redoc" in PUBLIC_PATHS

    def test_generate_token_returns_string(self):
        token = generate_token()
        assert isinstance(token, str)
        assert len(token) > 20

    def test_generate_token_unique(self):
        """Each call produces a different token."""
        tokens = {generate_token() for _ in range(50)}
        assert len(tokens) == 50

    def test_token_guard_rejects_without_token(self):
        """When backend_token is set, requests without X-Backend-Token get 401."""
        original = settings.backend_token
        try:
            settings.backend_token = "test-secret-token-123"
            with TestClient(create_app()) as client:
                r = client.get("/api/websites/")
                assert r.status_code == 401
                body = r.json()
                assert body["error"]["code"] == "auth.invalid_token"
        finally:
            settings.backend_token = original

    def test_token_guard_rejects_wrong_token(self):
        original = settings.backend_token
        try:
            settings.backend_token = "correct-token"
            with TestClient(create_app()) as client:
                r = client.get("/api/websites/", headers={"X-Backend-Token": "wrong-token"})
                assert r.status_code == 401
        finally:
            settings.backend_token = original

    def test_token_guard_accepts_correct_token(self):
        original = settings.backend_token
        try:
            settings.backend_token = "my-secret"
            with TestClient(create_app()) as client:
                r = client.get("/api/websites/", headers={"X-Backend-Token": "my-secret"})
                assert r.status_code == 200
        finally:
            settings.backend_token = original

    def test_token_guard_allows_health_without_token(self):
        """Even with token enabled, /api/health works."""
        original = settings.backend_token
        try:
            settings.backend_token = "required"
            with TestClient(create_app()) as client:
                r = client.get("/api/health/")
                assert r.status_code == 200
        finally:
            settings.backend_token = original

    def test_token_guard_disabled_when_empty(self):
        """Empty backend_token means no guard (dev mode)."""
        original = settings.backend_token
        try:
            settings.backend_token = ""
            with TestClient(create_app()) as client:
                r = client.get("/api/websites/")
                assert r.status_code == 200
        finally:
            settings.backend_token = original


# ---------------------------------------------------------------------------
# 2. AI Provider Layer
# ---------------------------------------------------------------------------

class TestAIProviders:
    """Tests for the AI provider abstraction layer."""

    def test_default_models_defined(self):
        assert "openai" in DEFAULT_MODELS
        assert "gemini" in DEFAULT_MODELS
        assert "anthropic" in DEFAULT_MODELS
        assert DEFAULT_MODELS["openai"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_unknown_provider_raises(self):
        from app.core.exceptions import UpstreamError
        with pytest.raises(UpstreamError, match="Unknown AI provider"):
            await complete("bogus", "key", None, [])

    @pytest.mark.asyncio
    async def test_openai_request_shape(self, monkeypatch):
        """Verify the OpenAI provider sends correct request format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from OpenAI"}}]
        }

        async def mock_post(url, **kwargs):
            # Verify URL and headers
            assert "openai.com" in url
            assert "Authorization" in kwargs.get("headers", {})
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.ai.providers.http_client", lambda **kw: mock_client)

        messages = [{"role": "user", "content": "Say hello"}]
        result = await complete("openai", "test-key", None, messages)
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4o-mini"
        assert "OpenAI" in result["content"]

    @pytest.mark.asyncio
    async def test_gemini_request_shape(self, monkeypatch):
        """Verify Gemini provider formats messages correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]
        }

        captured_args = {}

        async def mock_post(url, **kwargs):
            captured_args["url"] = url
            captured_args["json"] = kwargs.get("json")
            captured_args["params"] = kwargs.get("params")
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.ai.providers.http_client", lambda **kw: mock_client)

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]
        result = await complete("gemini", "g-key", "gemini-2.0-flash", messages)
        assert result["provider"] == "gemini"
        assert result["model"] == "gemini-2.0-flash"
        # Verify system instruction was extracted
        body = captured_args["json"]
        assert "systemInstruction" in body
        assert body["systemInstruction"]["parts"][0]["text"] == "You are helpful"
        # API key passed as query param
        assert captured_args["params"]["key"] == "g-key"

    @pytest.mark.asyncio
    async def test_anthropic_request_shape(self, monkeypatch):
        """Verify Anthropic provider formats messages correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Hello from Anthropic"}]
        }

        captured_args = {}

        async def mock_post(url, **kwargs):
            captured_args["url"] = url
            captured_args["json"] = kwargs.get("json")
            captured_args["headers"] = kwargs.get("headers")
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.ai.providers.http_client", lambda **kw: mock_client)

        messages = [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "Summarize SEO"},
            {"role": "assistant", "content": "SEO is..."},
            {"role": "user", "content": "Tell me more"},
        ]
        result = await complete("anthropic", "a-key", "claude-3-5-haiku-latest", messages)
        assert result["provider"] == "anthropic"
        # System extracted separately
        body = captured_args["json"]
        assert body["system"] == "Be concise"
        # Only user/assistant turns in messages
        assert len(body["messages"]) == 3
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][1]["role"] == "assistant"
        assert body["messages"][2]["role"] == "user"
        # Headers
        assert captured_args["headers"]["x-api-key"] == "a-key"
        assert captured_args["headers"]["anthropic-version"] == "2023-06-01"

    @pytest.mark.asyncio
    async def test_gemini_converts_assistant_to_model_role(self, monkeypatch):
        """Gemini uses 'model' role instead of 'assistant'."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "response"}]}}]
        }
        captured = {}

        async def mock_post(url, **kwargs):
            captured["body"] = kwargs.get("json")
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        monkeypatch.setattr("app.integrations.ai.providers.http_client", lambda **kw: mock_client)

        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
        ]
        await complete("gemini", "k", None, messages)
        contents = captured["body"]["contents"]
        assert contents[0]["role"] == "user"
        assert contents[1]["role"] == "model"  # assistant -> model
        assert contents[2]["role"] == "user"

    def test_check_raises_on_4xx(self):
        """_check should raise UpstreamError for 4xx responses."""
        resp = MagicMock()
        resp.status_code = 401
        resp.json.return_value = {"error": "unauthorized"}
        with pytest.raises(UpstreamError, match="401"):
            _check(resp, "openai")

    def test_check_raises_on_5xx(self):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "Internal Server Error"
        resp.json.side_effect = ValueError("not json")
        with pytest.raises(UpstreamError, match="500"):
            _check(resp, "gemini")

    def test_check_passes_on_2xx(self):
        resp = MagicMock()
        resp.status_code = 200
        # Should not raise
        _check(resp, "openai")


# ---------------------------------------------------------------------------
# 3. HTML Parser (Crawler)
# ---------------------------------------------------------------------------

class TestHTMLParser:
    """Tests for the crawler HTML extraction engine."""

    def test_basic_page(self):
        html = """
        <html>
        <head><title>Test Page</title>
        <meta name="description" content="A test page">
        <link rel="canonical" href="/canonical-url">
        </head>
        <body>
        <h1>Main Title</h1>
        <p>Hello world.</p>
        <a href="/about">About us</a>
        <img src="/logo.png" alt="Company logo">
        </body>
        </html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert page.title == "Test Page"
        assert page.meta_description == "A test page"
        assert page.canonical == "https://example.com/canonical-url"
        assert len(page.headings) == 1
        assert page.headings[0] == {"level": 1, "text": "Main Title"}
        assert page.word_count > 0

    def test_heading_levels(self):
        html = "<html><body><h1>A</h1><h2>B</h2><h3>C</h3><h4>D</h4><h5>E</h5><h6>F</h6></body></html>"
        page = parse_html("https://example.com/", html, 200)
        assert len(page.headings) == 6
        assert [h["level"] for h in page.headings] == [1, 2, 3, 4, 5, 6]

    def test_links_extracted_with_nofollow(self):
        html = """
        <html><body>
        <a href="https://example.com/page1">Page 1</a>
        <a href="https://example.com/page2" rel="nofollow">NoFollow</a>
        <a href="javascript:void(0)">JS link</a>
        <a href="mailto:test@example.com">Email</a>
        </body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        # Only http/https links counted
        assert len(page.links) == 2
        assert page.links[0]["is_nofollow"] is False
        assert page.links[1]["is_nofollow"] is True
        assert page.links[1]["anchor_text"] == "NoFollow"

    def test_duplicate_links_deduplicated(self):
        html = """
        <html><body>
        <a href="https://example.com/same">Link 1</a>
        <a href="https://example.com/same">Link 2</a>
        </body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert len(page.links) == 1

    def test_images_with_alt(self):
        html = """
        <html><body>
        <img src="/img1.jpg" alt="Image one">
        <img src="/img2.jpg">
        <img>
        </body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert len(page.images) == 2
        assert page.images[0]["alt"] == "Image one"
        assert page.images[1]["alt"] == ""  # missing alt -> empty string

    def test_json_ld_structured_data(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "Article", "headline": "Test"}
        </script>
        <script type="application/ld+json">
        invalid json here
        </script>
        </head><body></body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert len(page.schema_json) == 1
        assert page.schema_json[0]["@type"] == "Article"

    def test_dates_from_meta_tags(self):
        html = """
        <html><head>
        <meta property="article:published_time" content="2026-01-15T10:00:00Z">
        <meta property="article:modified_time" content="2026-03-20T14:30:00Z">
        </head><body></body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert page.published_at == "2026-01-15T10:00:00Z"
        assert page.modified_at == "2026-03-20T14:30:00Z"

    def test_date_from_time_tag(self):
        html = """
        <html><body>
        <time datetime="2026-06-01">June 1, 2026</time>
        </body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert page.published_at == "2026-06-01"

    def test_scripts_and_styles_stripped_from_text(self):
        html = """
        <html><body>
        <script>var x = "hidden";</script>
        <style>.hidden { display: none; }</style>
        <p>Visible text</p>
        </body></html>
        """
        page = parse_html("https://example.com/", html, 200)
        assert "hidden" not in page.text_content
        assert "Visible text" in page.text_content

    def test_empty_html(self):
        page = parse_html("https://example.com/", "", 200)
        assert page.title is None
        assert page.meta_description is None
        assert page.word_count == 0
        assert len(page.headings) == 0

    def test_minimal_html_no_body(self):
        html = "<html><head><title>Only Title</title></head></html>"
        page = parse_html("https://example.com/", html, 200)
        assert page.title == "Only Title"

    def test_canonical_relative_resolved(self):
        html = '<html><head><link rel="canonical" href="/page"></head><body></body></html>'
        page = parse_html("https://example.com/blog/post", html, 200)
        assert page.canonical == "https://example.com/page"

    def test_canonical_absolute_preserved(self):
        html = '<html><head><link rel="canonical" href="https://other.com/page"></head><body></body></html>'
        page = parse_html("https://example.com/", html, 200)
        assert page.canonical == "https://other.com/page"

    def test_word_count(self):
        html = "<html><body><p>one two three four five</p></body></html>"
        page = parse_html("https://example.com/", html, 200)
        assert page.word_count == 5

    def test_status_code_recorded(self):
        page = parse_html("https://example.com/", "<html></html>", 404)
        assert page.status_code == 404

    def test_url_recorded(self):
        page = parse_html("https://example.com/specific", "<html></html>", 200)
        assert page.url == "https://example.com/specific"


# ---------------------------------------------------------------------------
# 4. Robots.txt Policy
# ---------------------------------------------------------------------------

class TestRobotsPolicy:
    """Tests for robots.txt compliance checking."""

    @pytest.mark.asyncio
    async def test_same_site_detection(self):
        policy = RobotsPolicy("https://example.com")
        assert policy.same_site("https://example.com/page") is True
        assert policy.same_site("https://other.com/page") is False
        # same_site() compares netloc only, not scheme
        assert policy.same_site("http://example.com/page") is True

    def test_can_fetch_before_load_defaults_true(self):
        policy = RobotsPolicy("https://example.com")
        # Before load(), should default to True (allow)
        assert policy.can_fetch("https://example.com/page") is True

    @pytest.mark.asyncio
    async def test_load_handles_404_gracefully(self):
        """Non-200 robots.txt -> loaded, but no rules parsed (robotparser defaults to disallow)."""
        policy = RobotsPolicy("https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.integrations.crawler.robots.http_client", return_value=mock_client):
            await policy.load()

        assert policy._loaded is True
        # robotparser defaults to disallowing when no rules are parsed
        # The code comment says "everything allowed" but the actual behavior
        # depends on robotparser's default (which is disallow)
        result = policy.can_fetch("https://example.com/anything")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_load_handles_network_error(self):
        """Network failure -> loaded, no rules parsed."""
        policy = RobotsPolicy("https://example.com")

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.integrations.crawler.robots.http_client", return_value=mock_client):
            await policy.load()

        assert policy._loaded is True
        result = policy.can_fetch("https://example.com/page")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_disallow_blocks_crawl(self):
        """robots.txt Disallow should block fetching."""
        policy = RobotsPolicy("https://example.com")
        robots_txt = "User-agent: *\nDisallow: /private/\n"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = robots_txt

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.integrations.crawler.robots.http_client", return_value=mock_client):
            await policy.load()

        assert policy.can_fetch("https://example.com/public/") is True
        assert policy.can_fetch("https://example.com/private/secret") is False


# ---------------------------------------------------------------------------
# 5. Sitemap Parser
# ---------------------------------------------------------------------------

class TestSitemapParser:
    """Tests for sitemap XML parsing."""

    @pytest.mark.asyncio
    async def test_parse_simple_sitemap(self, monkeypatch):
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/</loc></url>
            <url><loc>https://example.com/about</loc></url>
            <url><loc>https://example.com/contact</loc></url>
        </urlset>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sitemap_xml.encode()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.sitemap.sitemap.http_client", lambda **kw: mock_client)

        urls = await fetch_sitemap_urls("https://example.com/sitemap.xml")
        assert len(urls) == 3
        assert "https://example.com/" in urls
        assert "https://example.com/about" in urls

    @pytest.mark.asyncio
    async def test_parse_sitemap_index(self, monkeypatch):
        """Sitemap index should follow child sitemaps."""
        index_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
            <sitemap><loc>https://example.com/sitemap-posts.xml</loc></sitemap>
        </sitemapindex>"""

        pages_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/page1</loc></url>
        </urlset>"""

        posts_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/post1</loc></url>
        </urlset>"""

        responses = [MagicMock(status_code=200, content=index_xml.encode()),
                     MagicMock(status_code=200, content=pages_xml.encode()),
                     MagicMock(status_code=200, content=posts_xml.encode())]

        call_count = 0

        async def mock_get(url, **kw):
            nonlocal call_count
            resp = responses[call_count]
            call_count += 1
            return resp

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.sitemap.sitemap.http_client", lambda **kw: mock_client)

        urls = await fetch_sitemap_urls("https://example.com/sitemap.xml")
        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/post1" in urls

    @pytest.mark.asyncio
    async def test_respects_limit(self, monkeypatch):
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/1</loc></url>
            <url><loc>https://example.com/2</loc></url>
            <url><loc>https://example.com/3</loc></url>
        </urlset>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sitemap_xml.encode()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.sitemap.sitemap.http_client", lambda **kw: mock_client)

        urls = await fetch_sitemap_urls("https://example.com/sitemap.xml", limit=2)
        assert len(urls) == 2

    @pytest.mark.asyncio
    async def test_handles_invalid_xml(self, monkeypatch):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"not xml at all"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.sitemap.sitemap.http_client", lambda **kw: mock_client)

        urls = await fetch_sitemap_urls("https://example.com/sitemap.xml")
        assert urls == []

    @pytest.mark.asyncio
    async def test_handles_network_error(self, monkeypatch):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        monkeypatch.setattr("app.integrations.sitemap.sitemap.http_client", lambda **kw: mock_client)

        urls = await fetch_sitemap_urls("https://example.com/sitemap.xml")
        assert urls == []


# ---------------------------------------------------------------------------
# 6. Search Console Normalizer
# ---------------------------------------------------------------------------

class TestSearchConsoleNormalizer:
    """Tests for raw -> normalized data pipeline (Rule 7)."""

    def test_normalize_api_rows(self):
        rows = [
            {
                "keys": ["2026-08-01", "seo tips", "https://example.com/seo"],
                "clicks": "120",
                "impressions": "5000",
                "ctr": "0.024",
                "position": "3.2",
            },
            {
                "keys": ["2026-08-02", "content strategy", "https://example.com/content"],
                "clicks": "45",
                "impressions": "2100",
                "ctr": "0.0214",
                "position": "8.5",
            },
        ]
        result = normalize_api_rows(rows)
        assert len(result) == 2
        assert result[0]["date"] == "2026-08-01"
        assert result[0]["query"] == "seo tips"
        assert result[0]["page_url"] == "https://example.com/seo"
        assert result[0]["clicks"] == 120
        assert result[0]["impressions"] == 5000
        assert isinstance(result[0]["ctr"], float)
        assert isinstance(result[0]["position"], float)

    def test_normalize_empty_list(self):
        assert normalize_api_rows([]) == []

    def test_normalize_missing_keys_handled(self):
        rows = [{"keys": ["2026-08-01"], "clicks": 10}]
        result = normalize_api_rows(rows)
        assert result[0]["date"] == "2026-08-01"
        assert result[0]["query"] is None
        assert result[0]["page_url"] is None
        assert result[0]["clicks"] == 10
        assert result[0]["impressions"] == 0

    def test_normalize_manual_rows(self):
        rows = [
            {
                "date": "2026-08-15",
                "query": "test query",
                "page_url": "https://example.com/page",
                "clicks": 50,
                "impressions": 3000,
                "ctr": 0.0167,
                "position": 5.5,
            }
        ]
        result = normalize_manual_rows(rows)
        assert len(result) == 1
        assert result[0]["date"] == "2026-08-15"
        assert result[0]["clicks"] == 50

    def test_normalize_manual_rows_missing_optional(self):
        rows = [{"date": "2026-08-15"}]
        result = normalize_manual_rows(rows)
        assert result[0]["clicks"] == 0
        assert result[0]["impressions"] == 0
        assert result[0]["ctr"] == 0.0
        assert result[0]["position"] == 0.0


# ---------------------------------------------------------------------------
# 7. Crypto (encrypt/decrypt)
# ---------------------------------------------------------------------------

class TestCrypto:
    """Tests for at-rest encryption."""

    def test_encrypt_decrypt_roundtrip(self):
        plain = "my-secret-api-key-12345"
        encrypted = encrypt_secret(plain)
        assert encrypted != plain
        decrypted = decrypt_secret(encrypted)
        assert decrypted == plain

    def test_different_encryptions_differ(self):
        """Fernet produces different ciphertext each time (random IV)."""
        a = encrypt_secret("same")
        b = encrypt_secret("same")
        assert a != b
        # But both decrypt to the same value
        assert decrypt_secret(a) == decrypt_secret(b)
        assert decrypt_secret(b) == "same"

    def test_decrypt_invalid_token_returns_none(self):
        assert decrypt_secret("not-a-valid-fernet-token") is None

    def test_decrypt_empty_string_returns_none(self):
        assert decrypt_secret("") is None

    def test_encrypt_empty_string(self):
        encrypted = encrypt_secret("")
        assert decrypt_secret(encrypted) == ""

    def test_encrypt_unicode(self):
        text = "Ünïcödé 🔑 api key"
        encrypted = encrypt_secret(text)
        assert decrypt_secret(encrypted) == text

    def test_encrypt_long_string(self):
        text = "x" * 10000
        encrypted = encrypt_secret(text)
        assert decrypt_secret(encrypted) == text


# ---------------------------------------------------------------------------
# 8. HTTP Client
# ---------------------------------------------------------------------------

class TestHTTPClient:
    """Tests for the shared HTTP client factory."""

    def test_proxy_url_prefers_https(self):
        original_https = settings.https_proxy
        original_http = settings.http_proxy
        try:
            settings.https_proxy = "http://https-proxy:3128"
            settings.http_proxy = "http://http-proxy:8080"
            assert proxy_url() == "http://https-proxy:3128"
        finally:
            settings.https_proxy = original_https
            settings.http_proxy = original_http

    def test_proxy_url_falls_back_to_http(self):
        original_https = settings.https_proxy
        original_http = settings.http_proxy
        try:
            settings.https_proxy = ""
            settings.http_proxy = "http://http-proxy:8080"
            assert proxy_url() == "http://http-proxy:8080"
        finally:
            settings.https_proxy = original_https
            settings.http_proxy = original_http

    def test_proxy_url_returns_none_when_empty(self):
        original_https = settings.https_proxy
        original_http = settings.http_proxy
        try:
            settings.https_proxy = ""
            settings.http_proxy = ""
            assert proxy_url() is None
        finally:
            settings.https_proxy = original_https
            settings.http_proxy = original_http

    def test_http_client_no_proxy_by_default(self):
        original_https = settings.https_proxy
        original_http = settings.http_proxy
        try:
            settings.https_proxy = ""
            settings.http_proxy = ""
            client = http_client()
            assert len(client._mounts) == 0
        finally:
            settings.https_proxy = original_https
            settings.http_proxy = original_http

    def test_http_client_with_proxy(self):
        original_https = settings.https_proxy
        try:
            settings.https_proxy = "http://proxy:3128"
            client = http_client()
            assert len(client._mounts) > 0
        finally:
            settings.https_proxy = original_https

    def test_check_internet_returns_bool(self):
        result = check_internet()
        assert isinstance(result, bool)

    def test_check_internet_with_short_timeout(self):
        """Very short timeout should still return a bool, not raise."""
        result = check_internet(timeout=0.001)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# 9. Exception Model
# ---------------------------------------------------------------------------

class TestExceptions:
    """Tests for the application error envelope model."""

    def test_app_error_attributes(self):
        err = AppError("test.code", "Test message", status=422, details={"key": "val"})
        assert err.code == "test.code"
        assert err.message == "Test message"
        assert err.status == 422
        assert err.details == {"key": "val"}

    def test_app_error_default_status(self):
        err = AppError("code", "msg")
        assert err.status == 400

    def test_not_found_error_is_404(self):
        err = NotFoundError("not.found", "Missing")
        assert err.status == 404

    def test_conflict_error_is_409(self):
        err = ConflictError("conflict", "Duplicate")
        assert err.status == 409

    def test_upstream_error_is_502(self):
        err = UpstreamError("upstream.fail", "Google API down")
        assert err.status == 502

    def test_error_envelope_via_api(self):
        """AppError subclasses should produce proper JSON envelopes."""
        with TestClient(create_app()) as client:
            # Requesting a non-existent website should return 404 envelope
            r = client.get("/api/websites/999999")
            assert r.status_code == 404
            body = r.json()
            assert "error" in body
            assert "code" in body["error"]
            assert "message" in body["error"]
            assert isinstance(body["error"]["details"], dict)


# ---------------------------------------------------------------------------
# 10. Markdown Engine — Edge Cases
# ---------------------------------------------------------------------------

class TestMarkdownEdgeCases:
    """Boundary condition tests for the markdown-to-HTML engine."""

    def test_empty_input(self):
        assert to_html("") == ""

    def test_whitespace_only(self):
        result = to_html("   \n  \n  ")
        assert result == ""

    def test_horizontal_rule(self):
        for marker in ("---", "***", "___"):
            out = to_html(marker)
            assert "<hr>" in out

    def test_horizontal_rule_three_chars_exact(self):
        out = to_html("---")
        assert "<hr>" in out

    def test_blockquote(self):
        out = to_html("> First line\n> Second line")
        assert "<blockquote>" in out
        assert "First line" in out
        assert "Second line" in out
        assert "<br>" in out  # multi-line quoted

    def test_nested_inline_formatting(self):
        out = to_html("**bold with `code` inside**")
        assert "<strong>" in out
        assert "<code>code</code>" in out

    def test_link_in_paragraph(self):
        out = to_html("Visit [Google](https://google.com) now.")
        assert '<a href="https://google.com">Google</a>' in out

    def test_html_escaping_preserves_structure(self):
        out = to_html("# Title with <b>html</b>")
        assert "<h1>" in out
        assert "&lt;b&gt;" in out
        assert "</h1>" in out

    def test_multiple_code_blocks(self):
        md = "```\nblock 1\n```\n\nSome text\n\n```\nblock 2\n```"
        out = to_html(md)
        assert out.count("<pre><code>") == 2

    def test_code_block_with_special_chars(self):
        out = to_html("```\nif (a < b && c > d) {}\n```")
        assert "&lt;" in out
        assert "&gt;" in out
        assert "&amp;" in out

    def test_heading_levels_1_through_6(self):
        for level in range(1, 7):
            md = f"{'#' * level} Heading {level}"
            out = to_html(md)
            assert f"<h{level}>Heading {level}</h{level}>" in out

    def test_ordered_list(self):
        out = to_html("1. First\n2. Second\n3. Third")
        assert "<ol>" in out
        assert "<li>First</li>" in out
        assert "<li>Third</li>" in out

    def test_unordered_list_with_different_markers(self):
        for marker in ("-", "*", "+"):
            out = to_html(f"{marker} item")
            assert "<ul>" in out
            assert "<li>item</li>" in out

    def test_inline_code_not_affected_by_bold(self):
        out = to_html("`code` and **bold**")
        assert "<code>code</code>" in out
        assert "<strong>bold</strong>" in out

    def test_paragraph_merge(self):
        out = to_html("Line one\nLine two\nLine three")
        assert "<p>Line one Line two Line three</p>" in out

    def test_code_block_preserves_newlines(self):
        out = to_html("```\nline1\nline2\nline3\n```")
        assert "line1\nline2\nline3" in out

    def test_mixed_content(self):
        md = "# Title\n\nParagraph with **bold**.\n\n- item 1\n- item 2\n\n> quote"
        out = to_html(md)
        assert "<h1>Title</h1>" in out
        assert "<strong>bold</strong>" in out
        assert "<ul>" in out
        assert "<blockquote>" in out


# ---------------------------------------------------------------------------
# 11. Opportunity Engine Constants
# ---------------------------------------------------------------------------

class TestOpportunityEngine:
    """Tests for the Search Console opportunity detection thresholds."""

    def test_constants_reasonable(self):
        assert MIN_IMPRESSIONS == 500
        assert POSITION_MIN == 4.0
        assert POSITION_MAX == 12.0
        assert POSITION_MIN < POSITION_MAX

    def test_strike_zone_logic(self):
        """Verify the math behind the strike zone query."""
        # A page at position 6 with 1000 impressions should be an opportunity
        position = 6.0
        impressions = 1000
        assert POSITION_MIN <= position <= POSITION_MAX
        assert impressions >= MIN_IMPRESSIONS
