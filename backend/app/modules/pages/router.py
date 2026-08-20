"""Pages HTTP layer — crawled inventory, content, links."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.core.exceptions import NotFoundError
from app.modules.pages.repository import PagesRepository

router = APIRouter()


@router.get("/")
def list_pages(db: DbSession, pagination: PaginationDep, website_id: int | None = Query(None)):
    repo = PagesRepository(db)
    items, total = repo.list(website_id, pagination.offset, pagination.page_size)
    return page_response(items, total, pagination)


@router.get("/{page_id}")
def get_page(page_id: int, db: DbSession):
    repo = PagesRepository(db)
    page = repo.get(page_id)
    if not page:
        raise NotFoundError("page.not_found", f"Page {page_id} does not exist")
    return page


@router.get("/{page_id}/content")
def get_page_content(page_id: int, db: DbSession):
    content = PagesRepository(db).get_content(page_id)
    if not content:
        raise NotFoundError("page_content.not_found", f"No content stored for page {page_id}")
    return content


@router.get("/{page_id}/links")
def get_page_links(page_id: int, db: DbSession):
    return {"items": PagesRepository(db).get_links(page_id)}
