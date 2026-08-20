"""SEO opportunities HTTP layer (thin wrapper over the opportunity engine)."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.engines.search_console.opportunity_engine import find_page_opportunities

router = APIRouter()


@router.get("/")
def opportunities(db: DbSession, website_id: int = Query(...), days: int = Query(default=28, ge=7, le=365)):
    items = find_page_opportunities(db, website_id, days=days)
    return {"items": items, "total": len(items)}
