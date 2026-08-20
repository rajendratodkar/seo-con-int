"""Page Speed HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.page_speed.schemas import PageSpeedCheck
from app.modules.page_speed.service import PageSpeedService

router = APIRouter()


def _svc(db: DbSession) -> PageSpeedService:
    return PageSpeedService(db)


@router.post("/check")
def check_page_speed(payload: PageSpeedCheck, db: DbSession):
    """Record a page speed measurement."""
    return _svc(db).check(payload.model_dump(exclude_none=True))


@router.get("/latest/{page_id}")
def latest(page_id: int, db: DbSession):
    """Get the latest speed data for a page."""
    return _svc(db).latest(page_id)


@router.get("/history/{page_id}")
def history(page_id: int, db: DbSession, limit: int = Query(30, ge=1, le=100)):
    """Get speed history for a page."""
    return _svc(db).history(page_id, limit)


@router.get("/summary")
def website_summary(db: DbSession, website_id: int = Query(...)):
    """Get average performance scores for a website."""
    return _svc(db).website_summary(website_id)


@router.get("/pagescores")
def pagescores(db: DbSession, website_id: int = Query(...), limit: int = Query(50, ge=1, le=200)):
    """Get latest score per page (sorted worst first)."""
    return _svc(db).pagescores(website_id, limit)
