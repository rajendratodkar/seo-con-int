"""Tests for Search Console File Upload module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import create_app  # noqa: E402


def _client():
    return TestClient(create_app())


# Sample CSV data
PERFORMANCE_CSV = """Date,Query,Page,Clicks,Impressions,CTR,Position
2026-08-15,seo best practices,https://example.com/seo-guide,142,5400,2.63%,8.2
2026-08-15,content marketing,https://example.com/content,89,3200,2.78%,12.5
2026-08-16,seo best practices,https://example.com/seo-guide,156,5800,2.69%,7.8
2026-08-16,keyword research,https://example.com/keywords,67,2100,3.19%,15.3
"""

PERFORMANCE_JSON = """{
  "rows": [
    {"keys": ["seo tips", "https://example.com/seo-tips"], "clicks": 200, "impressions": 8000, "ctr": 0.025, "position": 5.5},
    {"keys": ["content strategy", "https://example.com/content"], "clicks": 150, "impressions": 6000, "ctr": 0.025, "position": 8.2}
  ]
}"""

# Sample URL Inspection CSV
URL_INSPECTION_CSV = """URL,Coverage,Crawled as,Crawl allowed,Page fetch,Indexing,Last crawl
https://example.com/,Pass,Googlebot smartphone,Yes,Successful,Indexed,2026-08-10
https://example.com/about,Pass,Googlebot smartphone,Yes,Successful,Indexed,2026-08-10
https://example.com/old-page,Fail,Googlebot smartphone,No,Blocked by robots.txt,Not indexed,2026-08-01
https://example.com/draft,Excluded,Googlebot smartphone,Yes,Successful,Excluded - noindex,2026-08-05
"""

# Sample Coverage CSV
COVERAGE_CSV = """Status,Category,Count,Examples
Error,Submitted URL blocked by robots.txt,12,https://example.com/blocked
Error,Submitted URL returns 404,5,https://example.com/notfound
Valid,Submitted and indexed,342,
Warning,Crawled - currently not indexed,28,
Excluded,Excluded by noindex tag,15,
"""

# Sample Links CSV
LINKS_CSV = """Target Page,Source Page,Anchor Text,First Seen,Last Seen
https://example.com/,https://backlink1.com/article,Example Site,2026-01-15,2026-08-10
https://example.com/,https://backlink2.com/resources,click here,2026-03-20,2026-07-25
https://example.com/about,https://partner.com/team,About Page,2026-06-01,2026-08-12
"""


def _create_website(c, name, url):
    r = c.post("/api/websites/", json={"name": name, "url": url})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


class TestPerformanceImport:
    def test_upload_csv_performance(self):
        with _client() as c:
            site_id = _create_website(c, "SC Perf Test", "https://perf.example.com")
            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("performance.csv", PERFORMANCE_CSV, "text/csv")},
                data={"website_id": site_id, "import_type": "performance"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] == 4
            assert result["rows_errors"] == 0
            c.delete(f"/api/websites/{site_id}")

    def test_upload_json_performance(self):
        with _client() as c:
            site_id = _create_website(c, "SC JSON Test", "https://json.example.com")
            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("data.json", PERFORMANCE_JSON, "application/json")},
                data={"website_id": site_id, "import_type": "performance"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] == 2
            c.delete(f"/api/websites/{site_id}")


class TestUrlInspectionImport:
    def test_upload_csv_url_inspection(self):
        with _client() as c:
            site_id = _create_website(c, "SC Inspect Test", "https://inspect.example.com")
            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("url_inspection.csv", URL_INSPECTION_CSV, "text/csv")},
                data={"website_id": site_id, "import_type": "url_inspection"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] == 4
            assert result["rows_errors"] == 0
            c.delete(f"/api/websites/{site_id}")


class TestCoverageImport:
    def test_upload_csv_coverage(self):
        with _client() as c:
            site_id = _create_website(c, "SC Coverage Test", "https://coverage.example.com")
            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("coverage.csv", COVERAGE_CSV, "text/csv")},
                data={"website_id": site_id, "import_type": "coverage"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] == 5
            assert result["rows_errors"] == 0
            c.delete(f"/api/websites/{site_id}")


class TestLinksImport:
    def test_upload_csv_links(self):
        with _client() as c:
            site_id = _create_website(c, "SC Links Test", "https://links.example.com")
            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("links.csv", LINKS_CSV, "text/csv")},
                data={"website_id": site_id, "import_type": "links"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] == 3
            assert result["rows_errors"] == 0
            c.delete(f"/api/websites/{site_id}")


class TestScUploadImports:
    def test_list_imports(self):
        with _client() as c:
            r = c.get("/api/sc-upload/imports", params={"website_id": 1})
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_get_import_stats(self):
        with _client() as c:
            r = c.get("/api/sc-upload/stats", params={"website_id": 1})
            assert r.status_code == 200
            stats = r.json()
            assert "total_imports" in stats
