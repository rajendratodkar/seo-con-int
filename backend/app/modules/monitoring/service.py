"""Monitoring & Alerts service — orchestrates rule checks and alert delivery."""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.modules.monitoring.alerters import dispatch_alert
from app.modules.monitoring.checkers import run_checker
from app.modules.monitoring.repository import MonitoringRepository

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MonitoringRepository(db)

    # --- Channels -------------------------------------------------------------

    def create_channel(self, name: str, channel_type: str, config: dict) -> dict:
        return self.repo.create_channel(name, channel_type, config)

    def list_channels(self) -> list[dict]:
        return self.repo.list_channels()

    def get_channel(self, channel_id: int) -> dict:
        ch = self.repo.get_channel(channel_id)
        if not ch:
            raise NotFoundError("monitoring.channel_not_found", f"Channel {channel_id} not found")
        return ch

    def update_channel(self, channel_id: int, **fields) -> dict:
        ch = self.repo.update_channel(channel_id, **fields)
        if not ch:
            raise NotFoundError("monitoring.channel_not_found", f"Channel {channel_id} not found")
        return ch

    def delete_channel(self, channel_id: int) -> dict:
        ch = self.repo.get_channel(channel_id)
        if not ch:
            raise NotFoundError("monitoring.channel_not_found", f"Channel {channel_id} not found")
        self.repo.delete_channel(channel_id)
        return {"deleted": True, "id": channel_id}

    def test_channel(self, channel_id: int) -> dict:
        """Send a test notification to verify a channel works."""
        ch = self.repo.get_channel(channel_id)
        if not ch:
            raise NotFoundError("monitoring.channel_not_found", f"Channel {channel_id} not found")

        success, error = dispatch_alert(
            ch["channel_type"],
            json.loads(ch["config"]) if isinstance(ch["config"], str) else ch["config"],
            "Test notification",
            "This is a test alert from SEO Content Intelligence Monitor. "
            "If you see this, your channel is working correctly!",
            "info",
        )

        # Update last_tested_at
        self.repo.update_channel(channel_id, last_tested_at=datetime.now(timezone.utc).isoformat())

        return {"success": success, "error": error}

    # --- Rules ----------------------------------------------------------------

    def create_rule(
        self, website_id: int, name: str, rule_type: str,
        config: dict, channel_ids: list[int], check_interval: str,
    ) -> dict:
        # Validate channel ids exist
        for cid in channel_ids:
            if not self.repo.get_channel(cid):
                raise NotFoundError("monitoring.channel_not_found", f"Channel {cid} not found")
        return self.repo.create_rule(website_id, name, rule_type, config, channel_ids, check_interval)

    def list_rules(self, website_id: int | None = None) -> list[dict]:
        return self.repo.list_rules(website_id)

    def get_rule(self, rule_id: int) -> dict:
        rule = self.repo.get_rule(rule_id)
        if not rule:
            raise NotFoundError("monitoring.rule_not_found", f"Rule {rule_id} not found")
        return rule

    def update_rule(self, rule_id: int, **fields) -> dict:
        rule = self.repo.update_rule(rule_id, **fields)
        if not rule:
            raise NotFoundError("monitoring.rule_not_found", f"Rule {rule_id} not found")
        return rule

    def delete_rule(self, rule_id: int) -> dict:
        rule = self.repo.get_rule(rule_id)
        if not rule:
            raise NotFoundError("monitoring.rule_not_found", f"Rule {rule_id} not found")
        self.repo.delete_rule(rule_id)
        return {"deleted": True, "id": rule_id}

    # --- Run Checks -----------------------------------------------------------

    def run_rule_check(self, rule_id: int) -> dict:
        """Execute a single monitoring rule and send alerts if triggered."""
        rule = self.repo.get_rule(rule_id)
        if not rule:
            raise NotFoundError("monitoring.rule_not_found", f"Rule {rule_id} not found")

        config = json.loads(rule["config"]) if isinstance(rule["config"], str) else rule["config"]
        channel_ids = json.loads(rule["channel_ids"]) if isinstance(rule["channel_ids"], str) else rule["channel_ids"]

        # Run the checker
        alerts = run_checker(rule["rule_type"], self.db, rule["website_id"], config)

        # Mark rule as checked
        self.repo.mark_rule_checked(rule_id)

        # Send alerts through configured channels
        sent = 0
        failed = 0
        for alert in alerts:
            for cid in channel_ids:
                ch = self.repo.get_channel(cid)
                if not ch:
                    continue
                ch_config = json.loads(ch["config"]) if isinstance(ch["config"], str) else ch["config"]
                success, error = dispatch_alert(
                    ch["channel_type"], ch_config,
                    alert["title"], alert["message"], alert["severity"],
                )
                self.repo.log_alert(
                    rule_id=rule_id,
                    channel_id=cid,
                    severity=alert["severity"],
                    title=alert["title"],
                    message=alert["message"],
                    data=alert.get("data"),
                    status="sent" if success else "failed",
                    error_message=error,
                )
                if success:
                    sent += 1
                else:
                    failed += 1

        return {
            "rule_id": rule_id,
            "rule_name": rule["name"],
            "rule_type": rule["rule_type"],
            "alerts_triggered": len(alerts),
            "notifications_sent": sent,
            "notifications_failed": failed,
            "alerts": alerts,
        }

    def run_all_checks(self) -> dict:
        """Run all enabled rules that are due for checking."""
        rules = self.repo.list_enabled_rules()
        now = datetime.now(timezone.utc)
        results = []

        for rule in rules:
            # Check if rule is due
            last_checked = rule.get("last_checked_at")
            interval = rule.get("check_interval", "daily")
            if last_checked and not self._is_due(last_checked, interval, now):
                continue

            result = self.run_rule_check(rule["id"])
            results.append(result)

        return {
            "rules_checked": len(results),
            "total_alerts": sum(r["alerts_triggered"] for r in results),
            "results": results,
        }

    # --- History --------------------------------------------------------------

    def list_alert_history(self, rule_id: int | None = None, limit: int = 50) -> list[dict]:
        return self.repo.list_alert_history(rule_id, limit)

    def alert_stats(self) -> dict:
        return self.repo.alert_stats()

    # --- Snapshots (for future trend comparison) -----------------------------

    def save_snapshot(self, website_id: int, snapshot_type: str, data: dict) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.repo.save_snapshot(website_id, snapshot_type, today, data)

    # --- Helpers --------------------------------------------------------------

    @staticmethod
    def _is_due(last_checked: str, interval: str, now: datetime) -> bool:
        """Check if a rule is due for re-evaluation based on its interval."""
        try:
            last = datetime.fromisoformat(last_checked.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return True

        delta = (now - last).total_seconds()
        intervals = {
            "hourly": 3600,
            "daily": 86400,
            "weekly": 604800,
        }
        return delta >= intervals.get(interval, 86400)
