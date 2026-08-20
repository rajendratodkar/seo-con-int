"""Content Rewriter HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.content_rewriter.schemas import RewriteRequest, SelectRewrite
from app.modules.content_rewriter.service import ContentRewriterService

router = APIRouter()


def _svc(db: DbSession) -> ContentRewriterService:
    return ContentRewriterService(db)


@router.post("/rewrite")
def rewrite(payload: RewriteRequest, db: DbSession):
    """Generate AI-powered rewrites for content."""
    return _svc(db).rewrite(payload.model_dump())


@router.get("/history")
def history(
    db: DbSession,
    website_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Get rewrite history."""
    return _svc(db).history(website_id, limit)


@router.get("/{request_id}")
def get_rewrite(request_id: int, db: DbSession):
    """Get a specific rewrite request."""
    from app.core.exceptions import NotFoundError
    result = db.execute(
        __import__("sqlalchemy").text("SELECT * FROM rewrite_requests WHERE id = :id"),
        {"id": request_id},
    ).mappings().one_or_none()
    if not result:
        raise NotFoundError("rewriter.not_found", f"Request {request_id} not found")
    return dict(result)


@router.post("/{request_id}/select")
def select_rewrite(request_id: int, payload: SelectRewrite, db: DbSession):
    """Select a rewrite option."""
    return _svc(db).select(request_id, payload.selected_index)


@router.post("/{request_id}/apply")
def apply_rewrite(request_id: int, db: DbSession):
    """Mark a rewrite as applied."""
    return _svc(db).apply(request_id)
