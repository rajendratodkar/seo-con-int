"""Competitor Analysis HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.competitor_analysis.schemas import (
    CompetitorCreate,
    CompetitorUpdate,
    RankingBulkImport,
)
from app.modules.competitor_analysis.service import CompetitorService

router = APIRouter()


def _svc(db: DbSession) -> CompetitorService:
    return CompetitorService(db)


# ===========================================================================
# Competitors
# ===========================================================================

@router.post("", status_code=201)
def create_competitor(payload: CompetitorCreate, db: DbSession):
    """Add a competitor to track."""
    return _svc(db).create_competitor(payload.website_id, payload.name, payload.url, payload.notes)


@router.get("")
def list_competitors(db: DbSession, website_id: int = Query(..., description="Website ID")):
    """List all competitors for a website."""
    return _svc(db).list_competitors(website_id)


@router.get("/{competitor_id}")
def get_competitor(competitor_id: int, db: DbSession):
    """Get competitor detail with summary."""
    return _svc(db).competitor_summary(competitor_id)


@router.patch("/{competitor_id}")
def update_competitor(competitor_id: int, payload: CompetitorUpdate, db: DbSession):
    """Update competitor info."""
    return _svc(db).update_competitor(competitor_id, name=payload.name, notes=payload.notes)


@router.delete("/{competitor_id}")
def delete_competitor(competitor_id: int, db: DbSession):
    """Delete a competitor and all its data."""
    return _svc(db).delete_competitor(competitor_id)


# ===========================================================================
# Rankings
# ===========================================================================

@router.post("/{competitor_id}/rankings", status_code=201)
def import_rankings(competitor_id: int, payload: RankingBulkImport, db: DbSession):
    """Import keyword rankings for a competitor."""
    rankings = [r.model_dump() for r in payload.rankings]
    return _svc(db).import_rankings(competitor_id, rankings, payload.snapshot_date)


@router.get("/{competitor_id}/rankings")
def list_rankings(
    competitor_id: int, db: DbSession,
    limit: int = Query(200, ge=1, le=1000),
):
    """List keyword rankings for a competitor."""
    return _svc(db).list_rankings(competitor_id, limit)


# ===========================================================================
# Content Gaps
# ===========================================================================

@router.post("/{competitor_id}/gaps")
def analyze_gaps(competitor_id: int, db: DbSession, website_id: int = Query(...)):
    """Compute content gaps for a competitor vs our site."""
    return _svc(db).analyze_gaps(website_id, competitor_id)


@router.get("/gaps/all")
def list_gaps(
    db: DbSession,
    website_id: int = Query(...),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """List all content gaps for a website."""
    return _svc(db).list_gaps(website_id, status, limit)


@router.get("/gaps/stats")
def gap_stats(db: DbSession, website_id: int = Query(...)):
    """Get content gap statistics."""
    return _svc(db).gap_stats(website_id)


@router.patch("/gaps/{gap_id}/status")
def update_gap_status(gap_id: int, db: DbSession, status: str = Query(...)):
    """Update a content gap's status."""
    return _svc(db).update_gap_status(gap_id, status)


@router.delete("/gaps/{gap_id}")
def delete_gap(gap_id: int, db: DbSession):
    """Delete a content gap."""
    return _svc(db).delete_gap(gap_id)
