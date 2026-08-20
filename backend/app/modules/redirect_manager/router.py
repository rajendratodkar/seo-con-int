"""Redirect Manager HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.redirect_manager.service import RedirectManagerService
from app.modules.redirect_manager.schemas import (
    RedirectCreate, RedirectUpdate, RedirectBulkImport,
)

router = APIRouter()


@router.post("")
def create_redirect(db: DbSession, data: RedirectCreate):
    """Create a new redirect rule."""
    return RedirectManagerService(db).create(data)


@router.get("")
def list_redirects(
    db: DbSession,
    website_id: int = Query(...),
    status: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
):
    """List redirects for a website."""
    return RedirectManagerService(db).list(website_id, status, limit)


@router.get("/stats")
def redirect_stats(db: DbSession, website_id: int = Query(...)):
    """Get redirect statistics."""
    return RedirectManagerService(db).get_stats(website_id)


@router.get("/chains")
def detect_chains(db: DbSession, website_id: int = Query(...)):
    """Detect redirect chains (A→B→C)."""
    return RedirectManagerService(db).detect_chains(website_id)


@router.post("/bulk")
def bulk_import(db: DbSession, data: RedirectBulkImport):
    """Bulk import redirects (CSV-like format)."""
    return RedirectManagerService(db).bulk_import(data)


@router.get("/{redirect_id}")
def get_redirect(db: DbSession, redirect_id: int):
    """Get a specific redirect."""
    return RedirectManagerService(db).get(redirect_id)


@router.patch("/{redirect_id}")
def update_redirect(db: DbSession, redirect_id: int, data: RedirectUpdate):
    """Update a redirect rule."""
    return RedirectManagerService(db).update(redirect_id, data)


@router.delete("/{redirect_id}")
def delete_redirect(db: DbSession, redirect_id: int):
    """Delete a redirect rule."""
    return RedirectManagerService(db).delete(redirect_id)


@router.post("/{redirect_id}/check")
def record_check(
    db: DbSession,
    redirect_id: int,
    status_code: int | None = Query(None),
    response_time_ms: int | None = Query(None),
    final_url: str | None = Query(None),
    error_message: str | None = Query(None),
):
    """Record a redirect check result."""
    return RedirectManagerService(db).record_check(
        redirect_id, status_code, response_time_ms, final_url, error_message
    )


@router.get("/{redirect_id}/history")
def check_history(db: DbSession, redirect_id: int, limit: int = Query(20, ge=1, le=100)):
    """Get check history for a redirect."""
    return RedirectManagerService(db).get_check_history(redirect_id)


@router.post("/{redirect_id}/resolve-chain")
def resolve_chain(db: DbSession, redirect_id: int):
    """Resolve a redirect chain by pointing to the final destination."""
    return RedirectManagerService(db).resolve_chain(redirect_id)
