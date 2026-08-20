"""Content Refresh HTTP layer."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.api.dependencies import DbSession
from app.modules.content_refresh.service import ContentRefreshService
from app.modules.content_refresh.schemas import RefreshRuleCreate, RefreshRuleUpdate

router = APIRouter()


# --- Rules ---

@router.post("/rules")
def create_rule(db: DbSession, data: RefreshRuleCreate):
    """Create a refresh rule for a website."""
    return ContentRefreshService(db).create_rule(
        data.website_id, data.name, data.min_age_days,
        data.traffic_drop_pct, data.staleness_weight, data.traffic_weight,
    )


@router.get("/rules")
def list_rules(db: DbSession, website_id: int = Query(...)):
    """List all refresh rules for a website."""
    return ContentRefreshService(db).list_rules(website_id)


@router.patch("/rules/{rule_id}")
def update_rule(db: DbSession, rule_id: int, data: RefreshRuleUpdate):
    """Update a refresh rule."""
    return ContentRefreshService(db).update_rule(rule_id, data.model_dump(exclude_unset=True))


@router.delete("/rules/{rule_id}")
def delete_rule(db: DbSession, rule_id: int):
    """Delete a refresh rule."""
    return ContentRefreshService(db).delete_rule(rule_id)


# --- Scan & Schedule ---

@router.post("/scan")
def run_scan(db: DbSession, website_id: int = Query(...), rule_id: int | None = Query(None)):
    """Run a staleness scan and create refresh schedules."""
    return ContentRefreshService(db).run_scan(website_id, rule_id)


@router.get("/schedule")
def list_schedules(db: DbSession, website_id: int = Query(...), status: str | None = Query(None)):
    """List refresh schedules for a website."""
    return ContentRefreshService(db).list_schedules(website_id, status)


@router.get("/schedule/{schedule_id}")
def get_schedule(db: DbSession, schedule_id: int):
    """Get a specific refresh schedule."""
    return ContentRefreshService(db).get_schedule(schedule_id)


@router.patch("/schedule/{schedule_id}/status")
def update_schedule_status(db: DbSession, schedule_id: int, status: str = Query(...)):
    """Update schedule status (in_progress, completed, skipped)."""
    return ContentRefreshService(db).update_schedule_status(schedule_id, status)


@router.post("/schedule/{schedule_id}/skip")
def skip_schedule(db: DbSession, schedule_id: int):
    """Skip a refresh schedule."""
    return ContentRefreshService(db).skip_schedule(schedule_id)


@router.post("/schedule/{schedule_id}/complete")
def complete_schedule(db: DbSession, schedule_id: int):
    """Mark a refresh as completed."""
    return ContentRefreshService(db).complete_schedule(schedule_id)


@router.delete("/schedule/{schedule_id}")
def delete_schedule(db: DbSession, schedule_id: int):
    """Delete a refresh schedule."""
    return ContentRefreshService(db).delete_schedule(schedule_id)


# --- History & Stats ---

@router.get("/history")
def list_history(db: DbSession, website_id: int = Query(...)):
    """List refresh history for a website."""
    return ContentRefreshService(db).list_history(website_id)


@router.get("/stats")
def get_stats(db: DbSession, website_id: int = Query(...)):
    """Get refresh statistics for a website."""
    return ContentRefreshService(db).get_stats(website_id)
