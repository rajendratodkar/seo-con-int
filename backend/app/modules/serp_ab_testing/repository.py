"""SERP A/B Testing repository — CRUD, snapshots, and statistical analysis."""
import math
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.serp_ab_testing.schemas import SERPTestCreate, SERPTestUpdate


class SERPABTestRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Tests CRUD
    # ------------------------------------------------------------------

    def create_test(self, data: SERPTestCreate) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO serp_ab_tests (website_id, page_id, name, status, "
                "control_title, control_description, variant_title, variant_description, "
                "min_duration_days, confidence_level) "
                "VALUES (:wid, :pid, :name, 'draft', :ct, :cd, :vt, :vd, :days, :conf) "
                "RETURNING *"
            ),
            {
                "wid": data.website_id,
                "pid": data.page_id,
                "name": data.name,
                "ct": data.control_title,
                "cd": data.control_description,
                "vt": data.variant_title,
                "vd": data.variant_description,
                "days": data.min_duration_days,
                "conf": data.confidence_level,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_test(self, test_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM serp_ab_tests WHERE id = :id"),
            {"id": test_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_tests_by_website(self, website_id: int, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM serp_ab_tests WHERE website_id = :wid"
        params: dict = {"wid": website_id}

        if status:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY created_at DESC"
        rows = self.db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def update_test(self, test_id: int, data: SERPTestUpdate) -> dict:
        updates = []
        params: dict = {"id": test_id}

        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name
        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status.value
            if data.status.value == "running":
                updates.append("started_at = datetime('now')")
            elif data.status.value in ("completed", "cancelled"):
                updates.append("completed_at = datetime('now')")
        if data.min_duration_days is not None:
            updates.append("min_duration_days = :days")
            params["days"] = data.min_duration_days
        if data.confidence_level is not None:
            updates.append("confidence_level = :conf")
            params["conf"] = data.confidence_level

        if not updates:
            return self.get_test(test_id)

        updates.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE serp_ab_tests SET {', '.join(updates)} WHERE id = :id RETURNING *"),
            params,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_test(self, test_id: int) -> bool:
        # Delete snapshots first
        self.db.execute(
            text("DELETE FROM serp_ab_snapshots WHERE test_id = :id"),
            {"id": test_id},
        )
        result = self.db.execute(
            text("DELETE FROM serp_ab_tests WHERE id = :id"),
            {"id": test_id},
        )
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def add_snapshot(self, test_id: int, variant: str, snapshot_date: str,
                     clicks: int, impressions: int, ctr: float, avg_position: float) -> dict:
        # Check if snapshot exists for this date/variant
        existing = self.db.execute(
            text(
                "SELECT id FROM serp_ab_snapshots "
                "WHERE test_id = :tid AND variant = :var AND snapshot_date = :date"
            ),
            {"tid": test_id, "var": variant, "date": snapshot_date},
        ).mappings().first()

        if existing:
            # Update existing snapshot
            row = self.db.execute(
                text(
                    "UPDATE serp_ab_snapshots SET clicks = :clicks, impressions = :imp, "
                    "ctr = :ctr, avg_position = :pos WHERE id = :id RETURNING *"
                ),
                {"clicks": clicks, "imp": impressions, "ctr": ctr, "pos": avg_position, "id": existing["id"]},
            ).mappings().one()
        else:
            row = self.db.execute(
                text(
                    "INSERT INTO serp_ab_snapshots (test_id, variant, snapshot_date, clicks, impressions, ctr, avg_position) "
                    "VALUES (:tid, :var, :date, :clicks, :imp, :ctr, :pos) "
                    "RETURNING *"
                ),
                {"tid": test_id, "var": variant, "date": snapshot_date, "clicks": clicks,
                 "imp": impressions, "ctr": ctr, "pos": avg_position},
            ).mappings().one()

        self.db.commit()
        return dict(row)

    def get_snapshots(self, test_id: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM serp_ab_snapshots WHERE test_id = :tid "
                "ORDER BY snapshot_date ASC"
            ),
            {"tid": test_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_aggregated_metrics(self, test_id: int) -> dict:
        """Get aggregated metrics for control and variant."""
        result = {"control": {}, "variant": {}}

        for variant in ["control", "variant"]:
            row = self.db.execute(
                text(
                    "SELECT SUM(clicks) AS total_clicks, SUM(impressions) AS total_impressions, "
                    "CASE WHEN SUM(impressions) > 0 THEN CAST(SUM(clicks) AS REAL) / SUM(impressions) ELSE 0 END AS avg_ctr, "
                    "CASE WHEN SUM(impressions) > 0 THEN SUM(avg_position * impressions) / SUM(impressions) ELSE 0 END AS avg_position, "
                    "COUNT(*) AS days "
                    "FROM serp_ab_snapshots WHERE test_id = :tid AND variant = :var"
                ),
                {"tid": test_id, "var": variant},
            ).mappings().one()
            result[variant] = dict(row)

        return result

    # ------------------------------------------------------------------
    # Statistical Analysis
    # ------------------------------------------------------------------

    def calculate_z_test(self, test_id: int) -> dict:
        """Calculate two-proportion z-test for CTR difference."""
        metrics = self.get_aggregated_metrics(test_id)

        control = metrics["control"]
        variant = metrics["variant"]

        n1 = control.get("total_impressions", 0) or 0
        n2 = variant.get("total_impressions", 0) or 0
        x1 = control.get("total_clicks", 0) or 0
        x2 = variant.get("total_clicks", 0) or 0

        if n1 == 0 or n2 == 0:
            return {
                "z_score": 0, "p_value": 1, "is_significant": False,
                "control_ctr": 0, "variant_ctr": 0, "lift": 0,
            }

        p1 = x1 / n1  # Control CTR
        p2 = x2 / n2  # Variant CTR

        # Pooled proportion
        p_pool = (x1 + x2) / (n1 + n2)

        if p_pool == 0 or p_pool == 1:
            return {
                "z_score": 0, "p_value": 1, "is_significant": False,
                "control_ctr": p1, "variant_ctr": p2, "lift": 0,
            }

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

        if se == 0:
            return {
                "z_score": 0, "p_value": 1, "is_significant": False,
                "control_ctr": p1, "variant_ctr": p2, "lift": 0,
            }

        # Z-score
        z_score = (p2 - p1) / se

        # P-value (two-tailed)
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))

        # Lift
        lift = ((p2 - p1) / p1 * 100) if p1 > 0 else 0

        return {
            "z_score": round(z_score, 4),
            "p_value": round(p_value, 6),
            "control_ctr": round(p1, 4),
            "variant_ctr": round(p2, 4),
            "lift": round(lift, 2),
        }

    def _normal_cdf(self, x: float) -> float:
        """Approximate cumulative distribution function for standard normal."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, website_id: int) -> dict:
        total = self.db.execute(
            text("SELECT COUNT(*) FROM serp_ab_tests WHERE website_id = :wid"),
            {"wid": website_id},
        ).scalar()

        running = self.db.execute(
            text("SELECT COUNT(*) FROM serp_ab_tests WHERE website_id = :wid AND status = 'running'"),
            {"wid": website_id},
        ).scalar()

        completed = self.db.execute(
            text("SELECT COUNT(*) FROM serp_ab_tests WHERE website_id = :wid AND status = 'completed'"),
            {"wid": website_id},
        ).scalar()

        control_wins = self.db.execute(
            text("SELECT COUNT(*) FROM serp_ab_tests WHERE website_id = :wid AND winner = 'control'"),
            {"wid": website_id},
        ).scalar()

        variant_wins = self.db.execute(
            text("SELECT COUNT(*) FROM serp_ab_tests WHERE website_id = :wid AND winner = 'variant'"),
            {"wid": website_id},
        ).scalar()

        inconclusive = self.db.execute(
            text("SELECT COUNT(*) FROM serp_ab_tests WHERE website_id = :wid AND winner = 'inconclusive'"),
            {"wid": website_id},
        ).scalar()

        avg_lift = self.db.execute(
            text("SELECT AVG(lift) FROM serp_ab_tests WHERE website_id = :wid AND lift IS NOT NULL"),
            {"wid": website_id},
        ).scalar()

        return {
            "total_tests": total,
            "running": running,
            "completed": completed,
            "control_wins": control_wins,
            "variant_wins": variant_wins,
            "inconclusive": inconclusive,
            "avg_lift": round(avg_lift, 2) if avg_lift else None,
        }
