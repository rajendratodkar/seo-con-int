"""Rank Tracker service — orchestrate keyword tracking, snapshots, and alerts."""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.rank_tracker.repository import RankTrackerRepository
from app.modules.rank_tracker.schemas import (
    TrackedKeywordCreate, TrackedKeywordUpdate, RankSnapshotCreate,
)


class RankTrackerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RankTrackerRepository(db)

    def create_keyword(self, data: TrackedKeywordCreate) -> dict:
        """Create a new tracked keyword."""
        return self.repo.create_keyword(data)

    def get_keyword(self, keyword_id: int) -> dict:
        keyword = self.repo.get_keyword(keyword_id)
        if not keyword:
            raise NotFoundError("keyword.not_found", f"Keyword {keyword_id} not found")
        return keyword

    def list_keywords(self, website_id: int, limit: int = 200) -> list[dict]:
        return self.repo.get_keywords_by_website(website_id, limit)

    def update_keyword(self, keyword_id: int, data: TrackedKeywordUpdate) -> dict:
        keyword = self.repo.get_keyword(keyword_id)
        if not keyword:
            raise NotFoundError("keyword.not_found", f"Keyword {keyword_id} not found")
        return self.repo.update_keyword(keyword_id, data)

    def delete_keyword(self, keyword_id: int) -> bool:
        keyword = self.repo.get_keyword(keyword_id)
        if not keyword:
            raise NotFoundError("keyword.not_found", f"Keyword {keyword_id} not found")
        return self.repo.delete_keyword(keyword_id)

    def add_snapshot(self, data: RankSnapshotCreate) -> dict:
        """Add a rank snapshot for a keyword."""
        keyword = self.repo.get_keyword(data.keyword_id)
        if not keyword:
            raise NotFoundError("keyword.not_found", f"Keyword {data.keyword_id} not found")
        return self.repo.add_snapshot(data.model_dump())

    def get_snapshots(self, keyword_id: int, limit: int = 90) -> list[dict]:
        """Get rank history for a keyword."""
        keyword = self.repo.get_keyword(keyword_id)
        if not keyword:
            raise NotFoundError("keyword.not_found", f"Keyword {keyword_id} not found")
        return self.repo.get_snapshots(keyword_id, limit)

    def get_stats(self, website_id: int) -> dict:
        """Get rank tracking statistics."""
        return self.repo.get_stats(website_id)

    def get_alerts(self, website_id: int, unread_only: bool = False) -> list[dict]:
        """Get rank change alerts."""
        return self.repo.get_alerts(website_id, unread_only)

    def mark_alert_read(self, alert_id: int) -> bool:
        """Mark an alert as read."""
        return self.repo.mark_alert_read(alert_id)

    def get_trends(self, website_id: int, days: int = 30) -> list[dict]:
        """Get position trends for all keywords."""
        return self.repo.get_website_trends(website_id, days)

    def get_keyword_trend(self, keyword_id: int, days: int = 30) -> list[dict]:
        """Get position trend for a single keyword."""
        keyword = self.repo.get_keyword(keyword_id)
        if not keyword:
            raise NotFoundError("keyword.not_found", f"Keyword {keyword_id} not found")
        return self.repo.get_keyword_trend(keyword_id, days)
