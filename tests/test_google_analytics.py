"""Google Analytics module tests: report parsing + error envelopes (no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402
from app.modules.google_analytics.service import GoogleAnalyticsService  # noqa: E402

FAKE_REPORT = {
    "dimensionHeaders": [{"name": "date"}],
    "metricHeaders": [{"name": "sessions"}, {"name": "activeUsers"}, {"name": "screenPageViews"}],
    "rows": [
        {"dimensionValues": [{"value": "20260815"}],
         "metricValues": [{"value": "12"}, {"value": "9"}, {"value": "31"}]},
        {"dimensionValues": [{"value": "20260816"}],
         "metricValues": [{"value": "7.0"}, {"value": "6"}, {"value": "15"}]},
    ],
}


def test_parse_report_normalizes_dates_and_values():
    rows = GoogleAnalyticsService._parse_report(FAKE_REPORT)
    assert rows[0] == {"date": "2026-08-15", "sessions": 12, "active_users": 9, "pageviews": 31}
    assert rows[1]["sessions"] == 7  # float strings tolerated


def test_summary_without_connection_returns_envelope():
    with TestClient(create_app()) as client:
        resp = client.get("/api/google-analytics/summary", params={"website_id": 999999})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ga.connection_not_found"


def test_connection_endpoints_respond():
    with TestClient(create_app()) as client:
        resp = client.get("/api/google-analytics/connection", params={"website_id": 1})
        assert resp.status_code == 200
        assert resp.json()["connection"] is None
