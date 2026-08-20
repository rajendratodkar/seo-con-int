"""Content Calendar HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.content_calendar.schemas import CalendarEventCreate, CalendarEventUpdate
from app.modules.content_calendar.service import ContentCalendarService

router = APIRouter()


def _svc(db: DbSession) -> ContentCalendarService:
    return ContentCalendarService(db)


@router.post("", status_code=201)
def create_event(payload: CalendarEventCreate, db: DbSession):
    """Create a calendar event."""
    return _svc(db).create_event(payload.model_dump(exclude_none=True))


@router.get("")
def list_events(
    db: DbSession,
    website_id: int = Query(...),
    start_date: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    status: str | None = Query(None),
    event_type: str | None = Query(None),
):
    """List calendar events with optional date range and status filters."""
    return _svc(db).list_events(website_id, start_date, end_date, status, event_type)


@router.get("/pipeline")
def pipeline(db: DbSession, website_id: int = Query(...)):
    """Get pipeline summary (counts by status)."""
    return _svc(db).pipeline(website_id)


@router.get("/deadlines")
def deadlines(db: DbSession, website_id: int = Query(...), days: int = Query(14, ge=1, le=90)):
    """Get upcoming deadlines."""
    return _svc(db).deadlines(website_id, days)


@router.get("/{event_id}")
def get_event(event_id: int, db: DbSession):
    """Get a single calendar event."""
    return _svc(db).get_event(event_id)


@router.patch("/{event_id}")
def update_event(event_id: int, payload: CalendarEventUpdate, db: DbSession):
    """Update a calendar event."""
    return _svc(db).update_event(event_id, **payload.model_dump(exclude_none=True))


@router.delete("/{event_id}")
def delete_event(event_id: int, db: DbSession):
    """Delete a calendar event."""
    return _svc(db).delete_event(event_id)
