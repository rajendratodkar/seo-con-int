"""Discussion HTTP layer."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.modules.discussion.service import DiscussionService

router = APIRouter()


class DiscussionCreate(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    website_id: int | None = None
    idea_id: int | None = None


class MessageSend(BaseModel):
    content: str = Field(min_length=1)
    ask_ai: bool = True
    provider: str | None = Field(default=None, pattern="^(openai|gemini|anthropic)$")


class DecisionCreate(BaseModel):
    decision: str = Field(min_length=3)
    rationale: str | None = None


@router.post("/")
def create(db: DbSession, payload: DiscussionCreate):
    return DiscussionService(db).create(payload.topic, payload.website_id, payload.idea_id)


@router.get("/")
def list_discussions(db: DbSession, pagination: PaginationDep):
    items, total = DiscussionService(db).list(pagination.page, pagination.page_size)
    return page_response(items, total, pagination)


@router.get("/{discussion_id}")
def get(db: DbSession, discussion_id: int):
    return DiscussionService(db).get(discussion_id)


@router.post("/{discussion_id}/messages")
async def send_message(db: DbSession, discussion_id: int, payload: MessageSend):
    return await DiscussionService(db).send_message(
        discussion_id, payload.content, payload.ask_ai, payload.provider
    )


@router.post("/{discussion_id}/decisions")
def decide(db: DbSession, discussion_id: int, payload: DecisionCreate):
    return DiscussionService(db).decide(discussion_id, payload.decision, payload.rationale)


@router.post("/{discussion_id}/archive")
def archive(db: DbSession, discussion_id: int):
    DiscussionService(db).archive(discussion_id)
    return {"id": discussion_id, "status": "archived"}
