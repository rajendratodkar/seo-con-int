"""Content drafting HTTP layer."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession
from app.modules.content.service import ContentService

router = APIRouter()


class DraftGenerate(BaseModel):
    plan_id: int
    provider: str | None = Field(default=None, pattern="^(openai|gemini|anthropic)$")


class DraftEdit(BaseModel):
    content: str = Field(min_length=1)


@router.get("/drafts")
def list_all_drafts(db: DbSession, status: str | None = None):
    items = ContentService(db).list_all_drafts(status)
    return {"items": items, "total": len(items)}


@router.post("/drafts/generate")
async def generate(db: DbSession, payload: DraftGenerate):
    return await ContentService(db).generate_draft(payload.plan_id, payload.provider)


@router.get("/plans/{plan_id}/drafts")
def list_drafts(db: DbSession, plan_id: int):
    items = ContentService(db).list_drafts(plan_id)
    return {"items": items, "total": len(items)}


@router.get("/drafts/{draft_id}")
def get_draft(db: DbSession, draft_id: int):
    return ContentService(db).get_draft(draft_id)


@router.put("/drafts/{draft_id}")
def edit_draft(db: DbSession, draft_id: int, payload: DraftEdit):
    return ContentService(db).edit_draft(draft_id, payload.content)


@router.post("/drafts/{draft_id}/approve")
def approve_draft(db: DbSession, draft_id: int):
    return ContentService(db).approve_draft(draft_id)
