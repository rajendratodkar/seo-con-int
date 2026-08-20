"""Internal links HTTP layer."""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.dependencies import DbSession
from app.modules.internal_links.service import InternalLinksService

router = APIRouter()


class LinkSave(BaseModel):
    website_id: int
    source_page_id: int
    target_page_id: int
    recommendation: str | None = None
    why: str | None = None


class StatusUpdate(BaseModel):
    status: str


@router.get("/suggestions")
def suggest(db: DbSession, website_id: int = Query(...), limit: int = Query(default=30, ge=1, le=100)):
    items = InternalLinksService(db).suggest(website_id, limit)
    return {"items": items, "total": len(items)}


@router.post("/")
def save(db: DbSession, payload: LinkSave):
    return InternalLinksService(db).save(
        payload.website_id, payload.source_page_id, payload.target_page_id,
        payload.recommendation, payload.why,
    )


@router.get("/")
def list_links(db: DbSession, website_id: int = Query(...), status: str | None = None):
    items = InternalLinksService(db).list(website_id, status)
    return {"items": items, "total": len(items)}


@router.patch("/{link_id}/status")
def set_status(db: DbSession, link_id: int, payload: StatusUpdate):
    return InternalLinksService(db).set_status(link_id, payload.status)
