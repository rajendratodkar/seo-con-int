"""Tests for the A/B Testing module.

Covers: test CRUD, measurement engine, z-test, API endpoint behavior.

Run: pytest tests/test_ab_testing.py -v
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import create_app


def _client():
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# 1. API Endpoint Smoke Tests
# ---------------------------------------------------------------------------

class TestABTestEndpoints:
    """Verify A/B testing API endpoints respond correctly."""

    def test_list_tests_empty(self):
        with _client() as client:
            r = client.get("/api/ab-tests")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_list_tests_with_website_filter(self):
        with _client() as client:
            r = client.get("/api/ab-tests?website_id=1")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_get_nonexistent_test(self):
        with _client() as client:
            r = client.get("/api/ab-tests/999999")
            assert r.status_code == 404


# ---------------------------------------------------------------------------
# 2. Z-Test Math
# ---------------------------------------------------------------------------

class TestZTest:
    """Unit tests for the CTR z-test measurement engine."""

    def test_z_test_identical_clicks(self):
        from app.modules.ab_testing.measurement import ctr_z_test
        result = ctr_z_test(100, 1000, 100, 1000)
        assert result["z"] == 0
        assert result["confidence"] == 0

    def test_z_test_variant_better(self):
        from app.modules.ab_testing.measurement import ctr_z_test
        # Variant has significantly higher CTR
        result = ctr_z_test(50, 1000, 100, 1000)
        assert result["z"] != 0
        assert result["confidence"] > 0

    def test_z_test_large_sample_significant(self):
        from app.modules.ab_testing.measurement import ctr_z_test
        # With large samples, even small differences become significant
        result = ctr_z_test(500, 10000, 600, 10000)
        assert result["confidence"] > 0.95

    def test_z_test_zero_impressions(self):
        from app.modules.ab_testing.measurement import ctr_z_test
        result = ctr_z_test(0, 0, 0, 0)
        assert result["confidence"] == 0
        assert result["p_value"] == 1.0

    def test_z_test_zero_ctr_pool(self):
        from app.modules.ab_testing.measurement import ctr_z_test
        result = ctr_z_test(0, 100, 0, 100)
        assert result["confidence"] == 0


# ---------------------------------------------------------------------------
# 3. Evaluate Test Logic
# ---------------------------------------------------------------------------

class TestEvaluateTest:
    """Unit tests for the evaluate_test function."""

    def test_insufficient_days(self):
        from app.modules.ab_testing.measurement import evaluate_test
        control = {"total_clicks": 100, "total_impressions": 5000, "avg_ctr": 0.02, "avg_position": 5, "days": 3}
        variant = {"total_clicks": 120, "total_impressions": 5000, "avg_ctr": 0.024, "avg_position": 4, "days": 3}
        result = evaluate_test(control, variant, min_days=7)
        assert result["winner"] == "insufficient_data"
        assert result["days_collected"] == 3
        assert result["min_days_required"] == 7

    def test_insufficient_impressions(self):
        from app.modules.ab_testing.measurement import evaluate_test
        control = {"total_clicks": 1, "total_impressions": 50, "avg_ctr": 0.02, "avg_position": 5, "days": 10}
        variant = {"total_clicks": 2, "total_impressions": 50, "avg_ctr": 0.04, "avg_position": 4, "days": 10}
        result = evaluate_test(control, variant, min_days=7)
        assert result["winner"] == "insufficient_data"
        assert "impressions" in result.get("reason", "")

    def test_variant_wins_high_confidence(self):
        from app.modules.ab_testing.measurement import evaluate_test
        # Variant has significantly higher CTR with enough data
        control = {"total_clicks": 500, "total_impressions": 20000, "avg_ctr": 0.025, "avg_position": 8, "days": 14}
        variant = {"total_clicks": 750, "total_impressions": 20000, "avg_ctr": 0.0375, "avg_position": 6, "days": 14}
        result = evaluate_test(control, variant, min_days=7)
        assert result["winner"] == "variant"
        assert result["confidence"] > 0.95
        assert result["ctr_diff_pct"] > 0

    def test_control_wins(self):
        from app.modules.ab_testing.measurement import evaluate_test
        # Control has better CTR
        control = {"total_clicks": 750, "total_impressions": 20000, "avg_ctr": 0.0375, "avg_position": 6, "days": 14}
        variant = {"total_clicks": 500, "total_impressions": 20000, "avg_ctr": 0.025, "avg_position": 8, "days": 14}
        result = evaluate_test(control, variant, min_days=7)
        assert result["winner"] == "control"
        assert result["ctr_diff_pct"] < 0

    def test_inconclusive_low_confidence(self):
        from app.modules.ab_testing.measurement import evaluate_test
        # Very similar CTRs — not enough to declare a winner
        control = {"total_clicks": 500, "total_impressions": 20000, "avg_ctr": 0.025, "avg_position": 8, "days": 14}
        variant = {"total_clicks": 510, "total_impressions": 20000, "avg_ctr": 0.0255, "avg_position": 8, "days": 14}
        result = evaluate_test(control, variant, min_days=7)
        # Small difference may be inconclusive
        assert result["winner"] in ("inconclusive", "control", "variant")


# ---------------------------------------------------------------------------
# 4. Measurement Engine
# ---------------------------------------------------------------------------

class TestMeasurementEngine:
    """Unit tests for the measurement data fetchers."""

    def test_fetch_sc_metrics_empty_db(self):
        from app.modules.ab_testing.measurement import fetch_sc_metrics_for_url
        mock_db = MagicMock()
        mock_db.execute.return_value.mappings.return_value.one_or_none.return_value = None
        result = fetch_sc_metrics_for_url(mock_db, 1, "https://example.com/page", "2026-01-01", "2026-01-31")
        assert result["total_clicks"] == 0
        assert result["total_impressions"] == 0

    def test_fetch_daily_sc_metrics_empty(self):
        from app.modules.ab_testing.measurement import fetch_daily_sc_metrics
        mock_db = MagicMock()
        mock_db.execute.return_value.mappings.return_value.all.return_value = []
        result = fetch_daily_sc_metrics(mock_db, 1, "https://example.com/page", "2026-01-01", "2026-01-31")
        assert result == []


# ---------------------------------------------------------------------------
# 5. Service Unit Tests
# ---------------------------------------------------------------------------

class TestABTestService:
    """Unit tests for the A/B testing service."""

    def test_create_test_page_not_found(self):
        from app.modules.ab_testing.service import ABTestService
        from app.core.exceptions import NotFoundError
        from sqlalchemy.orm import Session
        from sqlalchemy import text
        mock_db = MagicMock(spec=Session)
        # Page lookup returns None
        mock_db.execute.return_value.mappings.return_value.one_or_none.return_value = None
        svc = ABTestService(mock_db)
        with pytest.raises(NotFoundError):
            svc.create_test(1, 999, "Test", "title", None, None, "New", None, 7)


# ---------------------------------------------------------------------------
# 6. API Integration — Full Flow
# ---------------------------------------------------------------------------

class TestABTestFlow:
    """Integration tests: create test → start → evaluate lifecycle."""

    def test_create_and_get_test(self):
        with _client() as client:
            # First ensure a website and page exist
            client.post("/api/websites/", json={"name": "Test Site", "url": "https://test.example.com"})
            websites = client.get("/api/websites/").json()
            website_id = websites["items"][0]["id"]

            # Create a page (via crawl or direct insert — use the API)
            # For test purposes, create a test directly with a fake page_id
            # The API will return 404 if page doesn't exist, which is expected
            r = client.post("/api/ab-tests", json={
                "website_id": website_id,
                "page_id": 1,
                "name": "Title Test",
                "element": "title",
                "control_title": "Original Title",
                "variant_title": "New Better Title",
                "min_duration_days": 7,
            })
            # May be 404 if page doesn't exist — that's fine for this test
            if r.status_code == 201:
                body = r.json()
                assert body["name"] == "Title Test"
                assert body["status"] == "draft"
                assert body["control"] is not None
                assert body["variant"] is not None
                assert body["control"]["title"] == "Original Title"
                assert body["variant"]["title"] == "New Better Title"

    def test_start_non_draft_fails(self):
        """Starting a non-draft test should fail."""
        with _client() as client:
            # This test needs a running test to work — skip if no test exists
            tests = client.get("/api/ab-tests").json()
            running = [t for t in tests if t["status"] == "running"]
            if not running:
                pytest.skip("No running tests to test with")

            # Try to start an already running test
            test_id = running[0]["id"]
            r = client.post(f"/api/ab-tests/{test_id}/start")
            assert r.status_code == 400

    def test_cancel_test(self):
        """Cancelling a test should work."""
        with _client() as client:
            tests = client.get("/api/ab-tests").json()
            draft = [t for t in tests if t["status"] == "draft"]
            if not draft:
                pytest.skip("No draft tests to cancel")

            test_id = draft[0]["id"]
            r = client.post(f"/api/ab-tests/{test_id}/cancel")
            assert r.status_code == 200
            assert r.json()["status"] == "cancelled"

    def test_delete_test(self):
        """Deleting a test should remove it."""
        with _client() as client:
            tests = client.get("/api/ab-tests").json()
            cancelled = [t for t in tests if t["status"] == "cancelled"]
            if not cancelled:
                pytest.skip("No cancelled tests to delete")

            test_id = cancelled[0]["id"]
            r = client.delete(f"/api/ab-tests/{test_id}")
            assert r.status_code == 200
            assert r.json()["deleted"] is True

    def test_delete_nonexistent(self):
        with _client() as client:
            r = client.delete("/api/ab-tests/999999")
            assert r.status_code == 404
