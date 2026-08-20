"""Content ideas HTTP layer."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.core.exceptions import NotFoundError
from app.modules.content_ideas.service import ContentIdeasService, STATUSES

router = APIRouter()


class IdeaCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str | None = None
    website_id: int | None = None


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|validated|approved|rejected)$")


@router.post("/generate")
def generate(db: DbSession, website_id: int = Query(...)):
    items = ContentIdeasService(db).generate(website_id)
    return {"items": items, "total": len(items)}


@router.post("/")
def create_manual(db: DbSession, payload: IdeaCreate):
    return ContentIdeasService(db).create_manual(payload.website_id, payload.title, payload.description)


@router.get("/")
def list_ideas(
    db: DbSession,
    pagination: PaginationDep,
    website_id: int | None = None,
    status: str | None = Query(default=None, pattern="^(draft|validated|approved|rejected)$"),
):
    items, total = ContentIdeasService(db).list(pagination.page, pagination.page_size, website_id, status)
    return page_response(items, total, pagination)


@router.get("/{idea_id}")
def get_idea(db: DbSession, idea_id: int):
    idea = ContentIdeasService(db).get(idea_id)
    if idea is None:
        raise NotFoundError("idea.not_found", f"Content idea {idea_id} does not exist")
    return idea


@router.post("/{idea_id}/validate")
def validate_idea(db: DbSession, idea_id: int):
    return ContentIdeasService(db).validate(idea_id)


@router.patch("/{idea_id}/status")
def set_status(db: DbSession, idea_id: int, payload: StatusUpdate):
    return ContentIdeasService(db).set_status(idea_id, payload.status)


@router.delete("/{idea_id}")
def delete_idea(db: DbSession, idea_id: int):
    if not ContentIdeasService(db).delete(idea_id):
        raise NotFoundError("idea.not_found", f"Content idea {idea_id} does not exist")
    return {"deleted": idea_id}
