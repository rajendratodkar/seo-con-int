"""SERP A/B Testing HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.serp_ab_testing.service import SERPABTestService
from app.modules.serp_ab_testing.schemas import SERPTestCreate, SERPTestUpdate

router = APIRouter()


@router.post("")
def create_test(db: DbSession, data: SERPTestCreate):
    """Create a new SERP A/B test."""
    return SERPABTestService(db).create_test(data)


@router.get("")
def list_tests(
    db: DbSession,
    website_id: int = Query(...),
    status: str | None = Query(None),
):
    """List SERP A/B tests for a website."""
    return SERPABTestService(db).list_tests(website_id, status)


@router.get("/stats")
def get_stats(db: DbSession, website_id: int = Query(...)):
    """Get test statistics for a website."""
    return SERPABTestService(db).get_stats(website_id)


@router.get("/{test_id}")
def get_test(db: DbSession, test_id: int):
    """Get a specific SERP A/B test."""
    return SERPABTestService(db).get_test(test_id)


@router.patch("/{test_id}")
def update_test(db: DbSession, test_id: int, data: SERPTestUpdate):
    """Update a SERP A/B test."""
    return SERPABTestService(db).update_test(test_id, data)


@router.delete("/{test_id}")
def delete_test(db: DbSession, test_id: int):
    """Delete a SERP A/B test."""
    return SERPABTestService(db).delete_test(test_id)


@router.post("/{test_id}/start")
def start_test(db: DbSession, test_id: int):
    """Start a SERP A/B test."""
    return SERPABTestService(db).start_test(test_id)


@router.post("/{test_id}/pause")
def pause_test(db: DbSession, test_id: int):
    """Pause a running test."""
    return SERPABTestService(db).pause_test(test_id)


@router.post("/{test_id}/resume")
def resume_test(db: DbSession, test_id: int):
    """Resume a paused test."""
    return SERPABTestService(db).resume_test(test_id)


@router.post("/{test_id}/snapshots")
def add_snapshot(
    db: DbSession,
    test_id: int,
    variant: str = Query(...),
    snapshot_date: str = Query(...),
    clicks: int = Query(0),
    impressions: int = Query(0),
    ctr: float = Query(0.0),
    avg_position: float = Query(0.0),
):
    """Add a daily snapshot for a test variant."""
    return SERPABTestService(db).add_snapshot(
        test_id, variant, snapshot_date, clicks, impressions, ctr, avg_position
    )


@router.get("/{test_id}/snapshots")
def get_snapshots(db: DbSession, test_id: int):
    """Get all snapshots for a test."""
    return SERPABTestService(db).get_snapshots(test_id)


@router.post("/{test_id}/evaluate")
def evaluate_test(db: DbSession, test_id: int):
    """Evaluate test results using z-test."""
    return SERPABTestService(db).evaluate_test(test_id)
