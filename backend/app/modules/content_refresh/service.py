"""Content Refresh service — orchestrates engines and manages refresh workflow."""
import json
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.content_refresh.repository import ContentRefreshRepository
from app.engines.refresh.staleness_detector import detect_stale_pages
from app.engines.refresh.trend_analyzer import analyze_trends
from app.engines.refresh.priority_scorer import score_priority


class ContentRefreshService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContentRefreshRepository(self.db)

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    def create_rule(self, website_id: int, name: str, min_age_days: int = 90,
                    traffic_drop_pct: float = 10.0, staleness_weight: float = 1.0,
                    traffic_weight: float = 1.0) -> dict:
        return self.repo.create_rule(website_id, name, min_age_days, traffic_drop_pct,
                                     staleness_weight, traffic_weight)

    def list_rules(self, website_id: int) -> list[dict]:
        return self.repo.list_rules(website_id)

    def update_rule(self, rule_id: int, fields: dict) -> dict:
        rule = self.repo.get_rule(rule_id)
        if not rule:
            raise NotFoundError("rule.not_found", f"Rule {rule_id} not found")
        return self.repo.update_rule(rule_id, fields)

    def delete_rule(self, rule_id: int) -> bool:
        rule = self.repo.get_rule(rule_id)
        if not rule:
            raise NotFoundError("rule.not_found", f"Rule {rule_id} not found")
        return self.repo.delete_rule(rule_id)

    # ------------------------------------------------------------------
    # Scan & Schedule
    # ------------------------------------------------------------------

    def run_scan(self, website_id: int, rule_id: int | None = None) -> dict:
        """Run a staleness scan and create/refresh schedules."""
        # Get rules
        if rule_id:
            rule = self.repo.get_rule(rule_id)
            if not rule:
                raise NotFoundError("rule.not_found", f"Rule {rule_id} not found")
            rules = [rule]
        else:
            rules = [r for r in self.repo.list_rules(website_id) if r["enabled"]]
            if not rules:
                # Use defaults
                rules = [{"id": None, "min_age_days": 90, "traffic_drop_pct": 10.0,
                          "staleness_weight": 1.0, "traffic_weight": 1.0}]

        all_recommendations = []
        total_schedules = 0

        for rule in rules:
            # 1. Detect stale pages
            stale = detect_stale_pages(
                self.db, website_id,
                min_age_days=rule["min_age_days"],
            )

            # 2. Analyze trends
            page_ids = [s["page_id"] for s in stale]
            trends = analyze_trends(self.db, website_id, page_ids)

            # 3. Score priority
            scored = score_priority(
                stale, trends, self.db, website_id,
                weights={"staleness": rule["staleness_weight"], "traffic": rule["traffic_weight"], "findings": 0.25},
            )

            # 4. Create/update schedules
            for item in scored:
                if item["priority_score"] < 10:
                    continue  # Skip very low priority

                reason_parts = []
                for signal in item.get("signals", []):
                    reason_parts.append(signal.get("message", ""))
                reason = "; ".join(reason_parts) if reason_parts else "Page needs refresh"

                self.repo.upsert_schedule(
                    website_id=website_id,
                    page_id=item["page_id"],
                    rule_id=rule.get("id"),
                    priority_score=item["priority_score"],
                    priority_date=item["priority_date"],
                    reason=reason,
                    suggested_changes=item.get("suggested_changes", []),
                )
                total_schedules += 1

            all_recommendations.extend(scored)

        return {
            "pages_scanned": len(set(r.get("page_id") for r in all_recommendations)),
            "stale_pages_found": len([r for r in all_recommendations if r["priority_score"] > 10]),
            "schedules_created": total_schedules,
            "recommendations": all_recommendations[:50],  # cap response size
        }

    def list_schedules(self, website_id: int, status: str | None = None) -> list[dict]:
        return self.repo.list_schedules(website_id, status)

    def get_schedule(self, schedule_id: int) -> dict:
        schedule = self.repo.get_schedule(schedule_id)
        if not schedule:
            raise NotFoundError("schedule.not_found", f"Schedule {schedule_id} not found")
        return schedule

    def update_schedule_status(self, schedule_id: int, status: str) -> dict:
        schedule = self.repo.get_schedule(schedule_id)
        if not schedule:
            raise NotFoundError("schedule.not_found", f"Schedule {schedule_id} not found")
        return self.repo.update_schedule_status(schedule_id, status)

    def skip_schedule(self, schedule_id: int) -> dict:
        return self.update_schedule_status(schedule_id, "skipped")

    def complete_schedule(self, schedule_id: int, notes: str | None = None) -> dict:
        schedule = self.repo.get_schedule(schedule_id)
        if not schedule:
            raise NotFoundError("schedule.not_found", f"Schedule {schedule_id} not found")

        # Record in history
        self.repo.add_history(
            schedule_id=schedule_id,
            page_id=schedule["page_id"],
            action="refreshed",
            notes=notes,
        )

        return self.repo.update_schedule_status(schedule_id, "completed")

    def delete_schedule(self, schedule_id: int) -> bool:
        schedule = self.repo.get_schedule(schedule_id)
        if not schedule:
            raise NotFoundError("schedule.not_found", f"Schedule {schedule_id} not found")
        return self.repo.delete_schedule(schedule_id)

    # ------------------------------------------------------------------
    # History & Stats
    # ------------------------------------------------------------------

    def list_history(self, website_id: int) -> list[dict]:
        return self.repo.list_history(website_id)

    def get_stats(self, website_id: int) -> dict:
        return self.repo.get_stats(website_id)
