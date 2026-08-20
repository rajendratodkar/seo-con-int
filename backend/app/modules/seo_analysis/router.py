"""SEO analysis + findings HTTP layer (/api/seo/analysis and /api/findings)."""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.core.exceptions import NotFoundError
from app.modules.seo_analysis.repository import FindingsRepository
from app.modules.seo_analysis.service import SeoAnalysisService

analysis_router = APIRouter()
findings_router = APIRouter()


@analysis_router.post("/run")
def run_analysis(db: DbSession, website_id: int = Query(...)):
    return SeoAnalysisService(db).run(website_id)


@analysis_router.post("/opportunities/detect")
def detect_opportunities(db: DbSession, website_id: int = Query(...)):
    return SeoAnalysisService(db).detect_opportunities(website_id)


# --- findings (Recommendation objects) ---------------------------------------------------


@findings_router.get("/")
def list_findings(
    db: DbSession,
    pagination: PaginationDep,
    website_id: int | None = Query(None),
    rec_type: str | None = Query(None),
    status: str | None = Query(None),
):
    items, total = FindingsRepository(db).list(
        website_id, rec_type, status, pagination.offset, pagination.page_size
    )
    return page_response(items, total, pagination)


@findings_router.get("/{finding_id}")
def get_finding(finding_id: int, db: DbSession):
    finding = FindingsRepository(db).get(finding_id)
    if not finding:
        raise NotFoundError("finding.not_found", f"Finding {finding_id} does not exist")
    return finding


class StatusUpdate(BaseModel):
    status: str  # open | accepted | dismissed | resolved


@findings_router.patch("/{finding_id}/status")
def update_finding_status(finding_id: int, payload: StatusUpdate, db: DbSession):
    repo = FindingsRepository(db)
    if not repo.get(finding_id):
        raise NotFoundError("finding.not_found", f"Finding {finding_id} does not exist")
    repo.set_status(finding_id, payload.status)
    db.commit()
    return repo.get(finding_id)


class ActionCreate(BaseModel):
    action: str


@findings_router.post("/{finding_id}/actions", status_code=201)
def create_action(finding_id: int, payload: ActionCreate, db: DbSession):
    repo = FindingsRepository(db)
    if not repo.get(finding_id):
        raise NotFoundError("finding.not_found", f"Finding {finding_id} does not exist")
    action_id = repo.add_action(finding_id, payload.action)
    db.commit()
    return {"id": action_id, "finding_id": finding_id, "action": payload.action, "status": "pending"}
