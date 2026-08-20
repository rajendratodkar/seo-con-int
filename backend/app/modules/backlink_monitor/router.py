"""Backlink Monitor HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.backlink_monitor.schemas import BacklinkCreate, BacklinkImport, BacklinkUpdate
from app.modules.backlink_monitor.service import BacklinkService

router = APIRouter()


def _svc(db: DbSession) -> BacklinkService:
    return BacklinkService(db)


@router.post("", status_code=201)
def add_backlink(payload: BacklinkCreate, db: DbSession):
    """Add a single backlink."""
    return _svc(db).add_backlink(payload.model_dump())


@router.post("/import", status_code=201)
def import_backlinks(payload: BacklinkImport, db: DbSession):
    """Import multiple backlinks at once."""
    return _svc(db).import_backlinks([bl.model_dump() for bl in payload.backlinks])


@router.get("")
def list_backlinks(
    db: DbSession,
    website_id: int = Query(...),
    status: str | None = Query(None),
    domain: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """List backlinks with optional filters."""
    return _svc(db).list_backlinks(website_id, status, domain, limit)


@router.get("/profile")
def profile(db: DbSession, website_id: int = Query(...)):
    """Get backlink profile summary."""
    return _svc(db).profile(website_id)


@router.get("/changes")
def changes(db: DbSession, website_id: int = Query(...), limit: int = Query(50, ge=1, le=200)):
    """Get backlink change history."""
    return _svc(db).changes(website_id, limit)


@router.get("/{backlink_id}")
def get_backlink(backlink_id: int, db: DbSession):
    """Get a single backlink."""
    return _svc(db).get_backlink(backlink_id)


@router.patch("/{backlink_id}")
def update_backlink(backlink_id: int, payload: BacklinkUpdate, db: DbSession):
    """Update a backlink."""
    return _svc(db).update_backlink(backlink_id, **payload.model_dump(exclude_none=True))


@router.delete("/{backlink_id}")
def delete_backlink(backlink_id: int, db: DbSession):
    """Delete a backlink."""
    return _svc(db).delete_backlink(backlink_id)
