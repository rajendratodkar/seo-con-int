"""A/B Testing service — create tests, collect measurements, evaluate results."""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from sqlalchemy import text

from app.core.exceptions import AppError, NotFoundError
from app.modules.ab_testing.measurement import (
    evaluate_test,
    fetch_daily_sc_metrics,
    fetch_sc_metrics_for_url,
)
from app.modules.ab_testing.repository import ABTestRepository

logger = logging.getLogger(__name__)


class ABTestService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ABTestRepository(db)

    def create_test(
        self, website_id: int, page_id: int, name: str, element: str,
        control_title: str | None, control_description: str | None,
        variant_title: str | None, variant_description: str | None,
        min_duration_days: int,
    ) -> dict:
        """Create a new A/B test with control and variant."""
        # Validate the page exists
        page = self.db.execute(
            text("SELECT id, url FROM pages WHERE id = :pid AND website_id = :wid"),
            {"pid": page_id, "wid": website_id},
        ).mappings().one_or_none()
        if not page:
            raise NotFoundError("ab_testing.page_not_found", f"Page {page_id} not found")

        # Create the test
        test = self.repo.create_test(website_id, page_id, name, element, min_duration_days)

        # Create control variant (use current page values if not provided)
        self.repo.create_variant(
            test["id"], "control",
            control_title or page.get("title"),
            control_description,
        )

        # Create variant
        self.repo.create_variant(
            test["id"], "variant",
            variant_title,
            variant_description,
        )

        return self.get_test_detail(test["id"])

    def list_tests(self, website_id: int | None = None, status: str | None = None) -> list[dict]:
        return self.repo.list_tests(website_id, status)

    def get_test_detail(self, test_id: int) -> dict:
        """Get test with its variants."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("ab_testing.test_not_found", f"Test {test_id} not found")

        variants = self.repo.get_variants(test_id)
        control = next((v for v in variants if v["variant_type"] == "control"), None)
        variant = next((v for v in variants if v["variant_type"] == "variant"), None)

        # Parse result_summary if stored as JSON string
        result = dict(test)
        if isinstance(result.get("result_summary"), str):
            result["result_summary"] = json.loads(result["result_summary"])

        return {
            **result,
            "control": control,
            "variant": variant,
        }

    def start_test(self, test_id: int) -> dict:
        """Start a running test — sets status to 'running' and records start time."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("ab_testing.test_not_found", f"Test {test_id} not found")
        if test["status"] != "draft":
            raise AppError("ab_testing.already_started", "Test is not in draft status")

        now = datetime.now(timezone.utc).isoformat()
        self.repo.update_test(test_id, status="running", started_at=now)
        return self.get_test_detail(test_id)

    def collect_measurements(self, test_id: int) -> dict:
        """Pull latest SC data for both variants and store daily snapshots."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("ab_testing.test_not_found", f"Test {test_id} not found")

        # Get the page URL
        page = self.db.execute(
            text("SELECT url FROM pages WHERE id = :pid"), {"pid": test["page_id"]}
        ).mappings().one_or_none()
        if not page:
            raise AppError("ab_testing.page_missing", "Page no longer exists")

        url = page["url"]
        website_id = test["website_id"]

        # Fetch daily SC data for the page
        started = test.get("started_at", test["created_at"])
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        daily_data = fetch_daily_sc_metrics(db, website_id, url, started[:10], end)

        variants = self.repo.get_variants(test_id)
        snapshot_count = 0

        for variant in variants:
            for day in daily_data:
                self.repo.upsert_snapshot(
                    test_id, variant["id"], day["date"],
                    day["clicks"], day["impressions"], day["ctr"], day["position"],
                )
                snapshot_count += 1

        return {"snapshots_upserted": snapshot_count, "days_fetched": len(daily_data)}

    def evaluate_and_complete(self, test_id: int) -> dict:
        """Evaluate the test and mark it as completed if enough data exists."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("ab_testing.test_not_found", f"Test {test_id} not found")
        if test["status"] != "running":
            raise AppError("ab_testing.not_running", "Test is not running")

        # Collect latest measurements first
        self.collect_measurements(test_id)

        # Get aggregated metrics for both variants
        variants = self.repo.get_variants(test_id)
        control = next((v for v in variants if v["variant_type"] == "control"), None)
        variant = next((v for v in variants if v["variant_type"] == "variant"), None)

        control_metrics = self.repo.get_aggregated_metrics(test_id, control["id"])
        variant_metrics = self.repo.get_aggregated_metrics(test_id, variant["id"])

        # Evaluate
        result = evaluate_test(control_metrics, variant_metrics, test["min_duration_days"])

        if result["winner"] == "insufficient_data":
            return {
                "status": "running",
                "reason": result.get("reason", f"Need {result['min_days_required']} days, have {result['days_collected']}"),
                "days_collected": result["days_collected"],
                "min_days_required": result["min_days_required"],
            }

        # Complete the test
        now = datetime.now(timezone.utc).isoformat()
        self.repo.update_test(
            test_id,
            status="completed",
            completed_at=now,
            winner=result["winner"],
            confidence=result["confidence"],
            result_summary=result,
        )

        return self.get_test_detail(test_id)

    def cancel_test(self, test_id: int) -> dict:
        """Cancel a running test."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("ab_testing.test_not_found", f"Test {test_id} not found")
        if test["status"] not in ("draft", "running"):
            raise AppError("ab_testing.cannot_cancel", "Test is already completed or cancelled")

        self.repo.update_test(test_id, status="cancelled")
        return self.get_test_detail(test_id)

    def delete_test(self, test_id: int) -> dict:
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("ab_testing.test_not_found", f"Test {test_id} not found")
        self.repo.delete_test(test_id)
        return {"deleted": True, "id": test_id}



