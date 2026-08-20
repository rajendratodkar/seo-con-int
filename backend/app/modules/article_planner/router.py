"""Article planner HTTP layer."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.modules.article_planner.service import ArticlePlannerService

router = APIRouter()


class PlanFromIdea(BaseModel):
    idea_id: int
    website_id: int | None = None


class PlanManual(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    website_id: int | None = None
    audience: str | None = None


class BriefUpdate(BaseModel):
    title: str | None = None
    primary_topic: str | None = None
    search_intent: str | None = None
    audience: str | None = None
    outline: list | None = None
    questions: list | None = None
    internal_links: list | None = None
    sources: list | None = None
    facts_to_verify: list | None = None
    things_to_avoid: list | None = None


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|brief_ready|drafting|approved)$")


@router.post("/from-idea")
def from_idea(db: DbSession, payload: PlanFromIdea):
    return ArticlePlannerService(db).create_from_idea(payload.idea_id, payload.website_id)


@router.post("/")
def create_manual(db: DbSession, payload: PlanManual):
    return ArticlePlannerService(db).create_manual(payload.website_id, payload.title, payload.audience)


@router.get("/")
def list_plans(
    db: DbSession, pagination: PaginationDep,
    website_id: int | None = None, status: str | None = None,
):
    items, total = ArticlePlannerService(db).list(pagination.page, pagination.page_size, website_id, status)
    return page_response(items, total, pagination)


@router.get("/{plan_id}")
def get_plan(db: DbSession, plan_id: int):
    return ArticlePlannerService(db).get(plan_id)


@router.patch("/{plan_id}/brief")
def update_brief(db: DbSession, plan_id: int, payload: BriefUpdate):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    return ArticlePlannerService(db).update_brief(plan_id, fields)


@router.post("/{plan_id}/brief-ready")
def brief_ready(db: DbSession, plan_id: int):
    return ArticlePlannerService(db).mark_brief_ready(plan_id)


@router.patch("/{plan_id}/status")
def set_status(db: DbSession, plan_id: int, payload: StatusUpdate):
    return ArticlePlannerService(db).set_status(plan_id, payload.status)


@router.delete("/{plan_id}")
def delete_plan(db: DbSession, plan_id: int):
    from app.core.exceptions import NotFoundError
    if not ArticlePlannerService(db).delete(plan_id):
        raise NotFoundError("plan.not_found", f"Article plan {plan_id} does not exist")
    return {"deleted": plan_id}
