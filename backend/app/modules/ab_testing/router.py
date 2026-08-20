"""A/B Testing HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.ab_testing.schemas import (
    ABTestCompleteRequest,
    ABTestCreate,
    ABTestStartRequest,
    ABTestUpdate,
)
from app.modules.ab_testing.service import ABTestService

router = APIRouter()


def _svc(db: DbSession) -> ABTestService:
    return ABTestService(db)


@router.post("", status_code=201)
def create_test(payload: ABTestCreate, db: DbSession):
    """Create a new A/B test with control and variant."""
    return _svc(db).create_test(
        payload.website_id,
        payload.page_id,
        payload.name,
        payload.element,
        payload.control_title,
        payload.control_description,
        payload.variant_title,
        payload.variant_description,
        payload.min_duration_days,
    )


@router.get("")
def list_tests(
    db: DbSession,
    website_id: int | None = Query(None, description="Filter by website"),
    status: str | None = Query(None, description="Filter by status"),
):
    """List A/B tests."""
    return _svc(db).list_tests(website_id, status)


@router.get("/{test_id}")
def get_test(test_id: int, db: DbSession):
    """Get A/B test detail with variants and results."""
    return _svc(db).get_test_detail(test_id)


@router.patch("/{test_id}")
def update_test(test_id: int, payload: ABTestUpdate, db: DbSession):
    """Update A/B test settings (only for draft tests)."""
    return _svc(db).update_test(
        test_id,
        name=payload.name,
        min_duration_days=payload.min_duration_days,
    )


@router.post("/{test_id}/start")
def start_test(test_id: int, db: DbSession):
    """Start a draft A/B test."""
    return _svc(db).start_test(test_id)


@router.post("/{test_id}/collect")
def collect_measurements(test_id: int, db: DbSession):
    """Pull latest Search Console data for the test."""
    return _svc(db).collect_measurements(test_id)


@router.post("/{test_id}/evaluate")
def evaluate_test(test_id: int, db: DbSession):
    """Evaluate results and complete the test if enough data exists."""
    return _svc(db).evaluate_and_complete(test_id)


@router.post("/{test_id}/cancel")
def cancel_test(test_id: int, db: DbSession):
    """Cancel a running test."""
    return _svc(db).cancel_test(test_id)


@router.delete("/{test_id}")
def delete_test(test_id: int, db: DbSession):
    """Delete an A/B test and all its data."""
    return _svc(db).delete_test(test_id)
