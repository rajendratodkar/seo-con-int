"""Monitoring & Alerts HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.monitoring.schemas import (
    AlertChannelCreate,
    AlertChannelUpdate,
    MonitoringRuleCreate,
    MonitoringRuleUpdate,
    RunCheckRequest,
    TestChannelRequest,
)
from app.modules.monitoring.service import MonitoringService

router = APIRouter()


def _svc(db: DbSession) -> MonitoringService:
    return MonitoringService(db)


# ===========================================================================
# Channels
# ===========================================================================

@router.post("/channels", status_code=201)
def create_channel(payload: AlertChannelCreate, db: DbSession):
    """Create a new alert channel (email, slack, or desktop)."""
    return _svc(db).create_channel(payload.name, payload.channel_type, payload.config)


@router.get("/channels")
def list_channels(db: DbSession):
    """List all alert channels."""
    return _svc(db).list_channels()


@router.get("/channels/{channel_id}")
def get_channel(channel_id: int, db: DbSession):
    """Get a single alert channel."""
    return _svc(db).get_channel(channel_id)


@router.patch("/channels/{channel_id}")
def update_channel(channel_id: int, payload: AlertChannelUpdate, db: DbSession):
    """Update an alert channel."""
    return _svc(db).update_channel(
        channel_id,
        name=payload.name,
        enabled=payload.enabled,
        config=payload.config,
    )


@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: DbSession):
    """Delete an alert channel."""
    return _svc(db).delete_channel(channel_id)


@router.post("/channels/test")
def test_channel(payload: TestChannelRequest, db: DbSession):
    """Send a test notification to verify a channel works."""
    return _svc(db).test_channel(payload.channel_id)


# ===========================================================================
# Rules
# ===========================================================================

@router.post("/rules", status_code=201)
def create_rule(payload: MonitoringRuleCreate, db: DbSession):
    """Create a monitoring rule."""
    return _svc(db).create_rule(
        payload.website_id,
        payload.name,
        payload.rule_type,
        payload.config,
        payload.channel_ids,
        payload.check_interval,
    )


@router.get("/rules")
def list_rules(
    db: DbSession,
    website_id: int | None = Query(None, description="Filter by website"),
):
    """List monitoring rules, optionally filtered by website."""
    return _svc(db).list_rules(website_id)


@router.get("/rules/{rule_id}")
def get_rule(rule_id: int, db: DbSession):
    """Get a single monitoring rule."""
    return _svc(db).get_rule(rule_id)


@router.patch("/rules/{rule_id}")
def update_rule(rule_id: int, payload: MonitoringRuleUpdate, db: DbSession):
    """Update a monitoring rule."""
    return _svc(db).update_rule(
        rule_id,
        name=payload.name,
        enabled=payload.enabled,
        config=payload.config,
        channel_ids=payload.channel_ids,
        check_interval=payload.check_interval,
    )


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: DbSession):
    """Delete a monitoring rule."""
    return _svc(db).delete_rule(rule_id)


# ===========================================================================
# Checks
# ===========================================================================

@router.post("/check")
def run_single_check(payload: RunCheckRequest, db: DbSession):
    """Manually trigger a check for a specific rule."""
    return _svc(db).run_rule_check(payload.rule_id)


@router.post("/check/all", status_code=202)
def run_all_checks(db: DbSession):
    """Trigger checks for all enabled rules that are due."""
    return _svc(db).run_all_checks()


# ===========================================================================
# History
# ===========================================================================

@router.get("/history")
def list_alert_history(
    db: DbSession,
    rule_id: int | None = Query(None, description="Filter by rule"),
    limit: int = Query(50, ge=1, le=500),
):
    """List alert history."""
    return _svc(db).list_alert_history(rule_id, limit)


@router.get("/stats")
def alert_stats(db: DbSession):
    """Get alert statistics (counts by status and severity)."""
    return _svc(db).alert_stats()
