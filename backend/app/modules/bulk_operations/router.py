"""Bulk operations HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.bulk_operations.schemas import (
    BulkAnalyzeRequest,
    BulkCrawlRequest,
    BulkIdeaRequest,
)
from app.modules.bulk_operations.service import BulkOperationService

router = APIRouter()


def _service(db: DbSession) -> BulkOperationService:
    return BulkOperationService(db)


@router.post("/crawl", status_code=202)
def bulk_crawl(payload: BulkCrawlRequest, db: DbSession):
    """Start bulk crawl for multiple websites."""
    job_id = _service(db).start_bulk_crawl(
        payload.website_ids, payload.max_pages_per_site
    )
    return {
        "job_id": job_id,
        "status": "running",
        "operation": "bulk_crawl",
        "total_items": len(payload.website_ids),
    }


@router.post("/analyze", status_code=202)
def bulk_analyze(payload: BulkAnalyzeRequest, db: DbSession):
    """Start bulk SEO analysis for multiple websites."""
    job_id = _service(db).start_bulk_analyze(
        payload.website_ids, payload.page_limit
    )
    return {
        "job_id": job_id,
        "status": "running",
        "operation": "bulk_analyze",
        "total_items": len(payload.website_ids),
    }


@router.post("/ideas", status_code=202)
def bulk_ideas(payload: BulkIdeaRequest, db: DbSession):
    """Start bulk idea generation for multiple websites."""
    job_id = _service(db).start_bulk_ideas(
        payload.website_ids, payload.sources
    )
    return {
        "job_id": job_id,
        "status": "running",
        "operation": "bulk_ideas",
        "total_items": len(payload.website_ids),
    }


@router.get("/jobs")
def list_bulk_jobs(
    db: DbSession,
    operation: str | None = Query(None, description="Filter by operation type"),
    limit: int = Query(20, ge=1, le=100),
):
    """List bulk operation jobs."""
    return _service(db).list_jobs(operation=operation, limit=limit)


@router.get("/jobs/{job_id}")
def get_bulk_job(job_id: int, db: DbSession):
    """Get bulk operation job status."""
    return _service(db).get_job(job_id)
