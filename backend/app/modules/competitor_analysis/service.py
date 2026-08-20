"""Competitor Analysis service — manage competitors, rankings, and content gaps."""
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.competitor_analysis.gap_engine import compute_gaps
from app.modules.competitor_analysis.repository import CompetitorRepository

logger = logging.getLogger(__name__)


class CompetitorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CompetitorRepository(db)

    # --- Competitors ----------------------------------------------------------

    def create_competitor(self, website_id: int, name: str, url: str, notes: str | None) -> dict:
        # Normalize URL
        url = url.rstrip("/")
        return self.repo.create_competitor(website_id, name, url, notes)

    def list_competitors(self, website_id: int) -> list[dict]:
        return self.repo.list_competitors(website_id)

    def get_competitor(self, competitor_id: int) -> dict:
        c = self.repo.get_competitor(competitor_id)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")
        return c

    def update_competitor(self, competitor_id: int, **fields) -> dict:
        c = self.repo.update_competitor(competitor_id, **fields)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")
        return c

    def delete_competitor(self, competitor_id: int) -> dict:
        c = self.repo.get_competitor(competitor_id)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")
        self.repo.delete_competitor(competitor_id)
        return {"deleted": True, "id": competitor_id}

    # --- Rankings -------------------------------------------------------------

    def import_rankings(self, competitor_id: int, rankings: list[dict], snapshot_date: str) -> dict:
        """Import keyword rankings for a competitor."""
        c = self.repo.get_competitor(competitor_id)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")

        count = self.repo.bulk_upsert_rankings(competitor_id, rankings, snapshot_date)
        return {"imported": count, "competitor_id": competitor_id, "snapshot_date": snapshot_date}

    def list_rankings(self, competitor_id: int, limit: int = 200) -> list[dict]:
        c = self.repo.get_competitor(competitor_id)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")
        return self.repo.list_rankings(competitor_id, limit)

    def competitor_summary(self, competitor_id: int) -> dict:
        c = self.repo.get_competitor(competitor_id)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")

        rankings = self.repo.list_rankings(competitor_id, limit=50)
        avg_pos = None
        if rankings:
            avg_pos = sum(r["position"] for r in rankings) / len(rankings)

        return {
            "competitor": c,
            "keyword_count": len(rankings),
            "avg_position": round(avg_pos, 1) if avg_pos else None,
            "top_keywords": [
                {"keyword": r["keyword"], "position": r["position"], "url": r.get("url")}
                for r in rankings[:10]
            ],
        }

    # --- Content Gaps ---------------------------------------------------------

    def analyze_gaps(self, website_id: int, competitor_id: int) -> dict:
        """Compute content gaps for a specific competitor."""
        c = self.repo.get_competitor(competitor_id)
        if not c:
            raise NotFoundError("competitor.not_found", f"Competitor {competitor_id} not found")

        gaps = compute_gaps(self.db, website_id, competitor_id)

        # Upsert all gaps
        for gap in gaps:
            self.repo.upsert_gap(
                website_id=website_id,
                keyword=gap["keyword"],
                competitor_id=competitor_id,
                competitor_pos=gap["competitor_pos"],
                competitor_url=gap.get("competitor_url"),
                our_position=gap.get("our_position"),
                opportunity=gap["opportunity"],
                search_volume=gap.get("search_volume"),
                priority=gap["priority"],
            )

        return {
            "competitor_id": competitor_id,
            "competitor_name": c["name"],
            "gaps_found": len(gaps),
            "new_content": sum(1 for g in gaps if g["opportunity"] == "new_content"),
            "improve_existing": sum(1 for g in gaps if g["opportunity"] == "improve_existing"),
            "quick_win": sum(1 for g in gaps if g["opportunity"] == "quick_win"),
        }

    def list_gaps(self, website_id: int, status: str | None = None, limit: int = 100) -> list[dict]:
        return self.repo.list_gaps(website_id, status, limit)

    def gap_stats(self, website_id: int) -> dict:
        return self.repo.gap_stats(website_id)

    def update_gap_status(self, gap_id: int, status: str) -> dict:
        gap = self.repo.update_gap_status(gap_id, status)
        if not gap:
            raise NotFoundError("gap.not_found", f"Gap {gap_id} not found")
        return gap

    def delete_gap(self, gap_id: int) -> dict:
        if not self.repo.delete_gap(gap_id):
            raise NotFoundError("gap.not_found", f"Gap {gap_id} not found")
        return {"deleted": True, "id": gap_id}
