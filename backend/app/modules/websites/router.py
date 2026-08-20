"""Websites HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.modules.websites.schemas import WebsiteCreate, WebsiteUpdate
from app.modules.websites.service import WebsiteService

router = APIRouter()


def _service(db: DbSession) -> WebsiteService:
    return WebsiteService(db)


@router.get("/")
def list_websites(db: DbSession, pagination: PaginationDep):
    items, total = _service(db).list(pagination.offset, pagination.page_size)
    return page_response(items, total, pagination)


@router.post("/", status_code=201)
def create_website(payload: WebsiteCreate, db: DbSession):
    return _service(db).create(payload.name, payload.url, payload.sitemap_url)


@router.get("/{website_id}")
def get_website(website_id: int, db: DbSession):
    return _service(db).get(website_id)


@router.patch("/{website_id}")
def update_website(website_id: int, payload: WebsiteUpdate, db: DbSession):
    return _service(db).update(website_id, payload.model_dump())


@router.delete("/{website_id}", status_code=204)
def delete_website(website_id: int, db: DbSession):
    _service(db).delete(website_id)


@router.post("/{website_id}/test")
async def test_website(website_id: int, db: DbSession):
    return await _service(db).test(website_id)


@router.post("/{website_id}/detect")
async def detect_website(website_id: int, db: DbSession):
    return await _service(db).detect(website_id)


@router.post("/{website_id}/crawl/start", status_code=202)
def start_crawl(website_id: int, db: DbSession, max_pages: int = Query(500, ge=1, le=2000)):
    job_id = _service(db).start_crawl(website_id, max_pages)
    return {"job_id": job_id, "status": "running"}


@router.get("/crawl/{job_id}/status")
def crawl_status(job_id: int, db: DbSession):
    return _service(db).crawl_status(job_id)
