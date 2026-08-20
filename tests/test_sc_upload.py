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

# Sample JSON data
PERFORMANCE_JSON = """{
  "rows": [
    {"keys": ["seo tips", "https://example.com/seo-tips"], "clicks": 200, "impressions": 8000, "ctr": 0.025, "position": 5.5},
    {"keys": ["content strategy", "https://example.com/content"], "clicks": 150, "impressions": 6000, "ctr": 0.025, "position": 8.2}
  ]
}"""


class TestScUploadCSV:
    def test_upload_csv_performance(self):
        with _client() as c:
            # Create website first
            r = c.post("/api/websites/", json={"name": "SC Test", "url": "https://sc-test.example.com"})
            assert r.status_code in (200, 201), r.text
            site_id = r.json()["id"]

            # Upload CSV
            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("performance.csv", PERFORMANCE_CSV, "text/csv")},
                data={"website_id": site_id, "import_type": "performance"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] > 0
            assert result["rows_errors"] == 0

            # Cleanup
            c.delete(f"/api/websites/{site_id}")

    def test_upload_json_performance(self):
        with _client() as c:
            r = c.post("/api/websites/", json={"name": "SC JSON Test", "url": "https://sc-json.example.com"})
            assert r.status_code in (200, 201), r.text
            site_id = r.json()["id"]

            r = c.post(
                "/api/sc-upload/upload",
                files={"file": ("data.json", PERFORMANCE_JSON, "application/json")},
                data={"website_id": site_id, "import_type": "performance"},
            )
            assert r.status_code == 200, r.text
            result = r.json()
            assert result["rows_imported"] > 0

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
