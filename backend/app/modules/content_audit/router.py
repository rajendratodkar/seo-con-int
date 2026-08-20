"""Content audit HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.content_audit.service import ContentAuditService

router = APIRouter()


@router.get("/")
def audit(db: DbSession, website_id: int = Query(...)):
    items = ContentAuditService(db).audit(website_id)
    summary = {v: sum(1 for i in items if i["verdict"] == v) for v in
               ("keep", "improve", "refresh", "consolidate", "review")}
    return {"items": items, "summary": summary, "total": len(items)}
