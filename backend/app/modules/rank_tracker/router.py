"""Rank Tracker HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.rank_tracker.service import RankTrackerService
from app.modules.rank_tracker.schemas import (
    TrackedKeywordCreate, TrackedKeywordUpdate, RankSnapshotCreate,
)

router = APIRouter()


@router.post("/keywords")
def create_keyword(db: DbSession, data: TrackedKeywordCreate):
    """Add a new keyword to track."""
    return RankTrackerService(db).create_keyword(data)


@router.get("/keywords")
def list_keywords(db: DbSession, website_id: int = Query(...), limit: int = Query(200, ge=1, le=500)):
    """List tracked keywords for a website."""
    return RankTrackerService(db).list_keywords(website_id, limit)


@router.get("/stats")
def get_stats(db: DbSession, website_id: int = Query(...)):
    """Get rank tracking statistics."""
    return RankTrackerService(db).get_stats(website_id)


@router.get("/trends")
def get_trends(db: DbSession, website_id: int = Query(...), days: int = Query(30, ge=1, le=365)):
    """Get position trends for all keywords."""
    return RankTrackerService(db).get_trends(website_id, days)


@router.get("/alerts")
def get_alerts(
    db: DbSession,
    website_id: int = Query(...),
    unread_only: bool = Query(False),
):
    """Get rank change alerts."""
    return RankTrackerService(db).get_alerts(website_id, unread_only)


@router.get("/keywords/{keyword_id}")
def get_keyword(db: DbSession, keyword_id: int):
    """Get a specific tracked keyword."""
    return RankTrackerService(db).get_keyword(keyword_id)


@router.patch("/keywords/{keyword_id}")
def update_keyword(db: DbSession, keyword_id: int, data: TrackedKeywordUpdate):
    """Update a tracked keyword."""
    return RankTrackerService(db).update_keyword(keyword_id, data)


@router.delete("/keywords/{keyword_id}")
def delete_keyword(db: DbSession, keyword_id: int):
    """Delete a tracked keyword."""
    return RankTrackerService(db).delete_keyword(keyword_id)


@router.post("/snapshots")
def add_snapshot(db: DbSession, data: RankSnapshotCreate):
    """Add a rank snapshot for a keyword."""
    return RankTrackerService(db).add_snapshot(data)


@router.get("/keywords/{keyword_id}/snapshots")
def get_snapshots(db: DbSession, keyword_id: int, limit: int = Query(90, ge=1, le=365)):
    """Get rank history for a keyword."""
    return RankTrackerService(db).get_snapshots(keyword_id, limit)


@router.get("/keywords/{keyword_id}/trend")
def get_keyword_trend(db: DbSession, keyword_id: int, days: int = Query(30, ge=1, le=365)):
    """Get position trend for a single keyword."""
    return RankTrackerService(db).get_keyword_trend(keyword_id, days)


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(db: DbSession, alert_id: int):
    """Mark an alert as read."""
    return RankTrackerService(db).mark_alert_read(alert_id)
