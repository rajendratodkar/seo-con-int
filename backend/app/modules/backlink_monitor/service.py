"""Backlink Monitor service."""
import json
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.backlink_monitor.repository import BacklinkRepository

logger = logging.getLogger(__name__)


class BacklinkService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BacklinkRepository(db)
        self.repo.ensure_tables()

    def add_backlink(self, data: dict) -> dict:
        result = self.repo.create_backlink(data)
        if result:
            self.repo.log_change(
                data["website_id"], result.get("id"), "gained",
                data["source_url"], data["target_url"],
            )
        return result

    def import_backlinks(self, backlinks: list[dict]) -> dict:
        count = self.repo.bulk_create(backlinks)
        return {"imported": count}

    def list_backlinks(self, website_id: int, status: str | None = None, domain: str | None = None, limit: int = 100) -> list[dict]:
        return self.repo.list_backlinks(website_id, status, domain, limit)

    def get_backlink(self, backlink_id: int) -> dict:
        b = self.repo.get_backlink(backlink_id)
        if not b:
            raise NotFoundError("backlink.not_found", f"Backlink {backlink_id} not found")
        return b

    def update_backlink(self, backlink_id: int, **fields) -> dict:
        b = self.repo.update_backlink(backlink_id, **fields)
        if not b:
            raise NotFoundError("backlink.not_found", f"Backlink {backlink_id} not found")
        # Log status change
        if "status" in fields and fields["status"] in ("lost", "broken"):
            self.repo.log_change(
                b["website_id"], backlink_id, fields["status"],
                b["source_url"], b["target_url"],
                json.dumps({"new_status": fields["status"]}),
            )
        return b

    def delete_backlink(self, backlink_id: int) -> dict:
        b = self.repo.get_backlink(backlink_id)
        if not b:
            raise NotFoundError("backlink.not_found", f"Backlink {backlink_id} not found")
        self.repo.delete_backlink(backlink_id)
        return {"deleted": True, "id": backlink_id}

    def profile(self, website_id: int) -> dict:
        profile = self.repo.get_profile(website_id)
        changes = self.repo.list_changes(website_id, limit=10)
        return {**profile, "recent_changes": changes}

    def changes(self, website_id: int, limit: int = 50) -> list[dict]:
        return self.repo.list_changes(website_id, limit)
