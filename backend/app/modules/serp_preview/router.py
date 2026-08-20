"""SERP Preview HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.serp_preview.service import SERPPreviewService
from app.modules.serp_preview.schemas import SERPPreviewRequest, SERPBulkPreviewRequest

router = APIRouter()


@router.post("/preview")
def preview_SERP(db: DbSession, data: SERPPreviewRequest):
    """Generate a SERP preview from provided title, description, and URL."""
    return SERPPreviewService(db).generate_preview(data)


@router.get("/page/{page_id}")
def preview_page(db: DbSession, page_id: int):
    """Generate SERP preview for an existing page by ID."""
    return SERPPreviewService(db).preview_from_page(page_id)


@router.get("/website/{website_id}")
def preview_website(db: DbSession, website_id: int, limit: int = Query(50, ge=1, le=200)):
    """Generate SERP previews for all pages in a website."""
    return SERPPreviewService(db).bulk_preview(website_id, limit)


@router.put("/page/{page_id}")
def update_and_preview(
    db: DbSession,
    page_id: int,
    title: str | None = Query(None),
    meta_description: str | None = Query(None),
):
    """Update page title/description and return fresh SERP preview."""
    return SERPPreviewService(db).update_and_preview(page_id, title, meta_description)


@router.get("/website/{website_id}/bulk-score")
def bulk_score(db: DbSession, website_id: int, limit: int = Query(200, ge=1, le=500)):
    """Score all pages in a website with summary stats."""
    return SERPPreviewService(db).bulk_score(website_id, limit)
