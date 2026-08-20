"""Tests for the Monitoring & Alerts module.

Covers: channel CRUD, rule CRUD, checker logic, alerter dispatch,
and API endpoint behavior.

Run: pytest tests/test_monitoring.py -v
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import create_app


def _client():
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# 1. API Endpoint Smoke Tests
# ---------------------------------------------------------------------------

class TestMonitoringEndpoints:
    """Verify all monitoring API endpoints respond correctly."""

    def test_channels_list_empty(self):
        with _client() as client:
            r = client.get("/api/monitoring/channels")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_rules_list_empty(self):
        with _client() as client:
            r = client.get("/api/monitoring/rules")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_history_list_empty(self):
        with _client() as client:
            r = client.get("/api/monitoring/history")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_stats_returns_shape(self):
        with _client() as client:
            r = client.get("/api/monitoring/stats")
            assert r.status_code == 200
            body = r.json()
            assert "total" in body
            assert "by_status" in body
            assert "by_severity" in body


# ---------------------------------------------------------------------------
# 2. Channel CRUD
# ---------------------------------------------------------------------------

class TestChannelCRUD:
    """Test alert channel creation, update, and deletion via API."""

    def test_create_channel(self):
        with _client() as client:
            r = client.post("/api/monitoring/channels", json={
                "name": "Test Desktop",
                "channel_type": "desktop",
                "config": {},
            })
            assert r.status_code == 201
            body = r.json()
            assert body["name"] == "Test Desktop"
            assert body["channel_type"] == "desktop"
            assert body["enabled"] == 1  # SQLite stores as int
            assert "id" in body

    def test_create_email_channel(self):
        with _client() as client:
            r = client.post("/api/monitoring/channels", json={
                "name": "Email Alerts",
                "channel_type": "email",
                "config": {
                    "smtp_host": "smtp.example.com",
                    "from_address": "alerts@example.com",
                    "to_addresses": ["admin@example.com"],
                },
            })
            assert r.status_code == 201
            body = r.json()
            assert body["channel_type"] == "email"
            # config comes back as JSON string from SQLite
            config = json.loads(body["config"]) if isinstance(body["config"], str) else body["config"]
            assert config["smtp_host"] == "smtp.example.com"

    def test_create_slack_channel(self):
        with _client() as client:
            r = client.post("/api/monitoring/channels", json={
                "name": "Slack Alerts",
                "channel_type": "slack",
                "config": {"webhook_url": "https://hooks.slack.com/T00/B00/xxx"},
            })
            assert r.status_code == 201
            assert r.json()["channel_type"] == "slack"

    def test_create_invalid_type_rejected(self):
        with _client() as client:
            r = client.post("/api/monitoring/channels", json={
                "name": "Bad",
                "channel_type": "sms",
                "config": {},
            })
            assert r.status_code == 422  # validation error

    def test_list_channels(self):
        with _client() as client:
            client.post("/api/monitoring/channels", json={
                "name": "Ch1", "channel_type": "desktop", "config": {},
            })
            r = client.get("/api/monitoring/channels")
            assert r.status_code == 200
            assert len(r.json()) >= 1

    def test_get_channel(self):
        with _client() as client:
            created = client.post("/api/monitoring/channels", json={
                "name": "Get Me", "channel_type": "desktop", "config": {},
            }).json()
            r = client.get(f"/api/monitoring/channels/{created['id']}")
            assert r.status_code == 200
            assert r.json()["name"] == "Get Me"

    def test_get_nonexistent_channel(self):
        with _client() as client:
            r = client.get("/api/monitoring/channels/999999")
            assert r.status_code == 404

    def test_update_channel(self):
        with _client() as client:
            created = client.post("/api/monitoring/channels", json={
                "name": "Old Name", "channel_type": "desktop", "config": {},
            }).json()
            r = client.patch(f"/api/monitoring/channels/{created['id']}", json={
                "name": "New Name",
            })
            assert r.status_code == 200
            assert r.json()["name"] == "New Name"

    def test_disable_channel(self):
        with _client() as client:
            created = client.post("/api/monitoring/channels", json={
                "name": "Toggle", "channel_type": "desktop", "config": {},
            }).json()
            r = client.patch(f"/api/monitoring/channels/{created['id']}", json={
                "enabled": False,
            })
            assert r.status_code == 200
            assert r.json()["enabled"] == 0  # SQLite int

    def test_delete_channel(self):
        with _client() as client:
            created = client.post("/api/monitoring/channels", json={
                "name": "Delete Me", "channel_type": "desktop", "config": {},
            }).json()
            r = client.delete(f"/api/monitoring/channels/{created['id']}")
            assert r.status_code == 200
            assert r.json()["deleted"] is True
            # Verify gone
            r = client.get(f"/api/monitoring/channels/{created['id']}")
            assert r.status_code == 404

    def test_test_channel_desktop(self):
        with _client() as client:
            created = client.post("/api/monitoring/channels", json={
                "name": "Test Desktop", "channel_type": "desktop", "config": {},
            }).json()
            r = client.post("/api/monitoring/channels/test", json={
                "channel_id": created["id"],
            })
            assert r.status_code == 200
            assert r.json()["success"] is True


# ---------------------------------------------------------------------------
# 3. Rule CRUD
# ---------------------------------------------------------------------------

class TestRuleCRUD:
    """Test monitoring rule creation, update, and deletion via API."""

    def _create_channel(self, client) -> int:
        r = client.post("/api/monitoring/channels", json={
            "name": "Ch", "channel_type": "desktop", "config": {},
        })
        return r.json()["id"]

    def _get_website_id(self, client) -> int:
        r = client.get("/api/websites/")
        items = r.json().get("items", [])
        if items:
            return items[0]["id"]
        # Create one
        client.post("/api/websites/", json={"name": "Test", "url": "https://test.example.com"})
        r = client.get("/api/websites/")
        return r.json()["items"][0]["id"]

    def test_create_rule(self):
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            r = client.post("/api/monitoring/rules", json={
                "website_id": wid,
                "name": "Ranking Watch",
                "rule_type": "ranking_drop",
                "config": {"threshold_pct": 20},
                "channel_ids": [ch_id],
                "check_interval": "daily",
            })
            assert r.status_code == 201
            body = r.json()
            assert body["name"] == "Ranking Watch"
            assert body["rule_type"] == "ranking_drop"
            assert body["enabled"] == 1
            ch_ids = json.loads(body["channel_ids"]) if isinstance(body["channel_ids"], str) else body["channel_ids"]
            assert ch_ids == [ch_id]

    def test_create_all_rule_types(self):
        types = ["ranking_drop", "traffic_drop", "ctr_drop", "new_seo_issue", "crawl_error"]
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            for rt in types:
                r = client.post("/api/monitoring/rules", json={
                    "website_id": wid,
                    "name": f"Test {rt}",
                    "rule_type": rt,
                    "channel_ids": [ch_id],
                })
                assert r.status_code == 201, f"Failed for {rt}: {r.text}"

    def test_create_rule_invalid_type(self):
        with _client() as client:
            r = client.post("/api/monitoring/rules", json={
                "website_id": 1,
                "name": "Bad",
                "rule_type": "invalid_type",
                "channel_ids": [],
            })
            assert r.status_code == 422

    def test_create_rule_invalid_interval(self):
        with _client() as client:
            r = client.post("/api/monitoring/rules", json={
                "website_id": 1,
                "name": "Bad",
                "rule_type": "ranking_drop",
                "channel_ids": [],
                "check_interval": "minutely",
            })
            assert r.status_code == 422

    def test_list_rules(self):
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            client.post("/api/monitoring/rules", json={
                "website_id": wid, "name": "R1", "rule_type": "ranking_drop",
                "channel_ids": [ch_id],
            })
            r = client.get("/api/monitoring/rules")
            assert r.status_code == 200
            assert len(r.json()) >= 1

    def test_list_rules_by_website(self):
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            client.post("/api/monitoring/rules", json={
                "website_id": wid, "name": "R1", "rule_type": "ranking_drop",
                "channel_ids": [ch_id],
            })
            r = client.get(f"/api/monitoring/rules?website_id={wid}")
            assert r.status_code == 200
            names = [rule["name"] for rule in r.json()]
            assert "R1" in names

    def test_get_rule(self):
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            created = client.post("/api/monitoring/rules", json={
                "website_id": wid, "name": "Get Me", "rule_type": "ranking_drop",
                "channel_ids": [ch_id],
            }).json()
            r = client.get(f"/api/monitoring/rules/{created['id']}")
            assert r.status_code == 200
            assert r.json()["name"] == "Get Me"

    def test_get_nonexistent_rule(self):
        with _client() as client:
            r = client.get("/api/monitoring/rules/999999")
            assert r.status_code == 404

    def test_disable_rule(self):
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            created = client.post("/api/monitoring/rules", json={
                "website_id": wid, "name": "Toggle", "rule_type": "ranking_drop",
                "channel_ids": [ch_id],
            }).json()
            r = client.patch(f"/api/monitoring/rules/{created['id']}", json={"enabled": False})
            assert r.status_code == 200
            assert r.json()["enabled"] == 0

    def test_delete_rule(self):
        with _client() as client:
            ch_id = self._create_channel(client)
            wid = self._get_website_id(client)
            created = client.post("/api/monitoring/rules", json={
                "website_id": wid, "name": "Del", "rule_type": "ranking_drop",
                "channel_ids": [ch_id],
            }).json()
            r = client.delete(f"/api/monitoring/rules/{created['id']}")
            assert r.status_code == 200
            assert r.json()["deleted"] is True


# ---------------------------------------------------------------------------
# 4. Checker Unit Tests
# ---------------------------------------------------------------------------

class TestCheckers:
    """Unit tests for the monitoring checkers (no API calls)."""

    def test_checkers_dict_has_all_types(self):
        from app.modules.monitoring.checkers import CHECKERS
        expected = {"ranking_drop", "traffic_drop", "ctr_drop", "new_seo_issue", "crawl_error"}
        assert set(CHECKERS.keys()) == expected

    def test_run_checker_unknown_type_returns_empty(self):
        from app.modules.monitoring.checkers import run_checker
        from sqlalchemy.orm import Session
        # Mock DB session
        mock_db = MagicMock(spec=Session)
        result = run_checker("nonexistent", mock_db, 1, {})
        assert result == []

    def test_ranking_drop_checker_empty_db(self):
        from app.modules.monitoring.checkers import check_ranking_drop
        mock_db = MagicMock()
        mock_db.execute.return_value.mappings.return_value.all.return_value = []
        result = check_ranking_drop(mock_db, 1, {"threshold_pct": 15, "lookback_days": 7})
        assert result == []

    def test_traffic_drop_checker_no_previous_data(self):
        from app.modules.monitoring.checkers import check_traffic_drop
        mock_db = MagicMock()
        # First query (current) returns some clicks, second (previous) returns 0
        mock_db.execute.return_value.scalar.side_effect = [100, 0]
        result = check_traffic_drop(mock_db, 1, {"threshold_pct": 20, "lookback_days": 7})
        assert result == []  # No previous data = no alert

    def test_crawl_error_checker_empty_db(self):
        from app.modules.monitoring.checkers import check_crawl_errors
        mock_db = MagicMock()
        mock_db.execute.return_value.mappings.return_value.all.return_value = []
        result = check_crawl_errors(mock_db, 1, {"min_status_code": 400})
        assert result == []

    def test_new_seo_issues_checker_empty_db(self):
        from app.modules.monitoring.checkers import check_new_seo_issues
        mock_db = MagicMock()
        mock_db.execute.return_value.mappings.return_value.all.return_value = []
        result = check_new_seo_issues(mock_db, 1, {"min_severity": "warning"})
        assert result == []


# ---------------------------------------------------------------------------
# 5. Alerter Unit Tests
# ---------------------------------------------------------------------------

class TestAlerters:
    """Unit tests for the alerter dispatch functions."""

    def test_desktop_alerter_always_succeeds(self):
        from app.modules.monitoring.alerters import send_desktop
        success, error = send_desktop({}, "Test Title", "Test message", "info")
        assert success is True
        assert error is None

    def test_email_alerter_missing_config(self):
        from app.modules.monitoring.alerters import send_email
        success, error = send_email({}, "Title", "Msg", "warning")
        assert success is False
        assert "Missing" in error

    def test_slack_alerter_missing_webhook(self):
        from app.modules.monitoring.alerters import send_slack
        success, error = send_slack({}, "Title", "Msg", "critical")
        assert success is False
        assert "webhook_url" in error

    def test_dispatch_unknown_type(self):
        from app.modules.monitoring.alerters import dispatch_alert
        success, error = dispatch_alert("unknown", {}, "Title", "Msg", "info")
        assert success is False
        assert "Unknown" in error

    def test_alerters_dict_has_all_types(self):
        from app.modules.monitoring.alerters import ALERTERS
        assert set(ALERTERS.keys()) == {"email", "slack", "desktop"}


# ---------------------------------------------------------------------------
# 6. Service Unit Tests
# ---------------------------------------------------------------------------

class TestMonitoringService:
    """Unit tests for the monitoring service logic."""

    def test_create_channel_invalid_type(self):
        from app.modules.monitoring.service import MonitoringService
        from sqlalchemy.orm import Session
        mock_db = MagicMock(spec=Session)
        svc = MonitoringService(mock_db)
        # Should raise validation error from Pydantic
        with pytest.raises(Exception):
            from app.modules.monitoring.schemas import AlertChannelCreate
            AlertChannelCreate(name="Bad", channel_type="sms", config={})

    def test_is_due_hourly(self):
        from app.modules.monitoring.service import MonitoringService
        from datetime import datetime, timezone, timedelta
        # Last checked 2 hours ago — should be due
        last = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        assert MonitoringService._is_due(last, "hourly", datetime.now(timezone.utc)) is True
        # Last checked 5 minutes ago — not due
        last = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        assert MonitoringService._is_due(last, "hourly", datetime.now(timezone.utc)) is False

    def test_is_due_daily(self):
        from app.modules.monitoring.service import MonitoringService
        from datetime import datetime, timezone, timedelta
        # 2 days ago — due
        last = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        assert MonitoringService._is_due(last, "daily", datetime.now(timezone.utc)) is True
        # 12 hours ago — not due
        last = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        assert MonitoringService._is_due(last, "daily", datetime.now(timezone.utc)) is False

    def test_is_due_weekly(self):
        from app.modules.monitoring.service import MonitoringService
        from datetime import datetime, timezone, timedelta
        # 10 days ago — due
        last = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        assert MonitoringService._is_due(last, "weekly", datetime.now(timezone.utc)) is True
        # 3 days ago — not due
        last = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        assert MonitoringService._is_due(last, "weekly", datetime.now(timezone.utc)) is False

    def test_is_due_bad_date_returns_true(self):
        from app.modules.monitoring.service import MonitoringService
        from datetime import datetime, timezone
        assert MonitoringService._is_due("not-a-date", "daily", datetime.now(timezone.utc)) is True


# ---------------------------------------------------------------------------
# 7. History via API
# ---------------------------------------------------------------------------

class TestAlertHistory:
    """Test alert history listing and stats endpoints."""

    def test_history_empty(self):
        with _client() as client:
            r = client.get("/api/monitoring/history")
            assert r.status_code == 200
            assert isinstance(r.json(), list)

    def test_stats_shape(self):
        with _client() as client:
            r = client.get("/api/monitoring/stats")
            assert r.status_code == 200
            body = r.json()
            assert isinstance(body["total"], int)
            assert isinstance(body["by_status"], dict)
            assert isinstance(body["by_severity"], dict)
