"""Publishing HTTP layer (WordPress + GitHub/static site)."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession
from app.modules.publishing.service import PublishingService

router = APIRouter()


class ConfigPayload(BaseModel):
    site_url: str | None = None
    user: str | None = None
    app_password: str | None = None
    token: str | None = None
    repo: str | None = None
    branch: str | None = None
    path_template: str | None = None


class WordPressPublish(BaseModel):
    draft_id: int
    status: str = Field(default="draft", pattern="^(draft|publish)$")


class GitHubPublish(BaseModel):
    draft_id: int
    path: str | None = None
    message: str | None = None


@router.get("/config/{target}")
def get_config(db: DbSession, target: str):
    return PublishingService(db).get_config(target)


@router.put("/config/{target}")
def save_config(db: DbSession, target: str, payload: ConfigPayload):
    return PublishingService(db).save_config(target, payload.model_dump(exclude_none=True))


@router.post("/wordpress/test")
async def test_wordpress(db: DbSession):
    return await PublishingService(db).test_wordpress()


@router.post("/wordpress")
async def publish_wordpress(db: DbSession, payload: WordPressPublish):
    return await PublishingService(db).publish_wordpress(payload.draft_id, payload.status)


@router.post("/github")
async def publish_github(db: DbSession, payload: GitHubPublish):
    return await PublishingService(db).publish_github(payload.draft_id, payload.path, payload.message)


@router.get("/logs")
def list_logs(db: DbSession, draft_id: int | None = None, limit: int = 50):
    items = PublishingService(db).list_logs(draft_id, limit)
    return {"items": items, "total": len(items)}
