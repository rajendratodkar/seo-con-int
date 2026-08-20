"""Page Speed Insights service."""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.page_speed.repository import PageSpeedRepository

logger = logging.getLogger(__name__)


class PageSpeedService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PageSpeedRepository(db)
        self.repo.ensure_table()

    def check(self, data: dict) -> dict:
        """Record a page speed snapshot."""
        data["checked_at"] = datetime.now(timezone.utc).isoformat()
        return self.repo.save_snapshot(data)

    def latest(self, page_id: int) -> dict:
        result = self.repo.get_latest(page_id)
        if not result:
            raise NotFoundError("page_speed.no_data", f"No speed data for page {page_id}")
        return result

    def history(self, page_id: int, limit: int = 30) -> list[dict]:
        return self.repo.get_history(page_id, limit)

    def website_summary(self, website_id: int) -> dict:
        return self.repo.get_website_summary(website_id)

    def pagescores(self, website_id: int, limit: int = 50) -> list[dict]:
        return self.repo.get_pagescores(website_id, limit)
