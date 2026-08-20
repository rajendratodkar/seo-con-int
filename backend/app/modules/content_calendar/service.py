"""Content Calendar service."""
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.content_calendar.repository import CalendarRepository

logger = logging.getLogger(__name__)


class ContentCalendarService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CalendarRepository(db)
        self.repo.ensure_table()

    def create_event(self, data: dict) -> dict:
        return self.repo.create_event(data)

    def list_events(
        self, website_id: int, start_date: str | None = None, end_date: str | None = None,
        status: str | None = None, event_type: str | None = None,
    ) -> list[dict]:
        return self.repo.list_events(website_id, start_date, end_date, status, event_type)

    def get_event(self, event_id: int) -> dict:
        e = self.repo.get_event(event_id)
        if not e:
            raise NotFoundError("calendar.event_not_found", f"Event {event_id} not found")
        return e

    def update_event(self, event_id: int, **fields) -> dict:
        e = self.repo.update_event(event_id, **fields)
        if not e:
            raise NotFoundError("calendar.event_not_found", f"Event {event_id} not found")
        return e

    def delete_event(self, event_id: int) -> dict:
        if not self.repo.delete_event(event_id):
            raise NotFoundError("calendar.event_not_found", f"Event {event_id} not found")
        return {"deleted": True, "id": event_id}

    def pipeline(self, website_id: int) -> dict:
        return self.repo.pipeline_summary(website_id)

    def deadlines(self, website_id: int, days: int = 14) -> list[dict]:
        return self.repo.upcoming_deadlines(website_id, days)
