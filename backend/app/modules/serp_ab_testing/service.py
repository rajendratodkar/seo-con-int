"""SERP A/B Testing service — orchestrate tests, snapshots, and statistical analysis."""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.serp_ab_testing.repository import SERPABTestRepository
from app.modules.serp_ab_testing.schemas import SERPTestCreate, SERPTestUpdate, TestStatus


class SERPABTestService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SERPABTestRepository(db)

    def create_test(self, data: SERPTestCreate) -> dict:
        """Create a new SERP A/B test."""
        return self.repo.create_test(data)

    def get_test(self, test_id: int) -> dict:
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        return test

    def list_tests(self, website_id: int, status: str | None = None) -> list[dict]:
        return self.repo.get_tests_by_website(website_id, status)

    def update_test(self, test_id: int, data: SERPTestUpdate) -> dict:
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        return self.repo.update_test(test_id, data)

    def delete_test(self, test_id: int) -> bool:
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        return self.repo.delete_test(test_id)

    def start_test(self, test_id: int) -> dict:
        """Start a SERP A/B test."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        if test["status"] != "draft":
            raise ValueError("Only draft tests can be started")
        return self.repo.update_test(test_id, SERPTestUpdate(status=TestStatus.RUNNING))

    def pause_test(self, test_id: int) -> dict:
        """Pause a running test."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        if test["status"] != "running":
            raise ValueError("Only running tests can be paused")
        return self.repo.update_test(test_id, SERPTestUpdate(status=TestStatus.PAUSED))

    def resume_test(self, test_id: int) -> dict:
        """Resume a paused test."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        if test["status"] != "paused":
            raise ValueError("Only paused tests can be resumed")
        return self.repo.update_test(test_id, SERPTestUpdate(status=TestStatus.RUNNING))

    def add_snapshot(self, test_id: int, variant: str, snapshot_date: str,
                     clicks: int, impressions: int, ctr: float, avg_position: float) -> dict:
        """Add a daily snapshot for a test variant."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        if test["status"] != "running":
            raise ValueError("Can only add snapshots to running tests")
        return self.repo.add_snapshot(test_id, variant, snapshot_date, clicks, impressions, ctr, avg_position)

    def evaluate_test(self, test_id: int) -> dict:
        """Evaluate test results using z-test for statistical significance."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")

        # Calculate z-test
        z_result = self.repo.calculate_z_test(test_id)

        # Determine winner
        confidence_level = test.get("confidence_level", 0.95)
        is_significant = z_result["p_value"] < (1 - confidence_level)

        if is_significant:
            if z_result["variant_ctr"] > z_result["control_ctr"]:
                winner = "variant"
                recommendation = f"Variant wins! CTR improved by {z_result['lift']:.1f}% with {confidence_level*100:.0f}% confidence."
            else:
                winner = "control"
                recommendation = f"Control wins. Variant CTR was {abs(z_result['lift']):.1f}% lower."
        else:
            winner = "inconclusive"
            recommendation = f"Not enough data for statistical significance (p={z_result['p_value']:.4f}). Continue testing or increase sample size."

        # Update test with results
        self.repo.update_test(test_id, SERPTestUpdate(status=TestStatus.COMPLETED))

        # Store results in the test record
        self.db.execute(
            text(
                "UPDATE serp_ab_tests SET winner = :winner, confidence = :conf, "
                "z_score = :z, p_value = :p, lift = :lift, "
                "control_clicks = (SELECT COALESCE(SUM(clicks), 0) FROM serp_ab_snapshots WHERE test_id = :tid AND variant = 'control'), "
                "control_impressions = (SELECT COALESCE(SUM(impressions), 0) FROM serp_ab_snapshots WHERE test_id = :tid AND variant = 'control'), "
                "control_ctr = :ctrl_ctr, control_avg_position = :ctrl_pos, "
                "variant_clicks = (SELECT COALESCE(SUM(clicks), 0) FROM serp_ab_snapshots WHERE test_id = :tid AND variant = 'variant'), "
                "variant_impressions = (SELECT COALESCE(SUM(impressions), 0) FROM serp_ab_snapshots WHERE test_id = :tid AND variant = 'variant'), "
                "variant_ctr = :var_ctr, variant_avg_position = :var_pos "
                "WHERE id = :tid"
            ),
            {
                "tid": test_id,
                "winner": winner,
                "conf": z_result["p_value"],
                "z": z_result["z_score"],
                "p": z_result["p_value"],
                "lift": z_result["lift"],
                "ctrl_ctr": z_result["control_ctr"],
                "ctrl_pos": 0,  # Will be calculated from snapshots
                "var_ctr": z_result["variant_ctr"],
                "var_pos": 0,
            },
        )
        self.db.commit()

        return {
            "test_id": test_id,
            "winner": winner,
            "confidence": z_result["p_value"],
            "z_score": z_result["z_score"],
            "p_value": z_result["p_value"],
            "control_ctr": z_result["control_ctr"],
            "variant_ctr": z_result["variant_ctr"],
            "lift": z_result["lift"],
            "is_significant": is_significant,
            "recommendation": recommendation,
        }

    def get_snapshots(self, test_id: int) -> list[dict]:
        """Get all snapshots for a test."""
        test = self.repo.get_test(test_id)
        if not test:
            raise NotFoundError("test.not_found", f"Test {test_id} not found")
        return self.repo.get_snapshots(test_id)

    def get_stats(self, website_id: int) -> dict:
        """Get test statistics for a website."""
        return self.repo.get_stats(website_id)
