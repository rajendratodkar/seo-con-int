"""Research HTTP layer."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.core.exceptions import NotFoundError
from app.modules.research.service import ResearchService

router = APIRouter()


class SourceCreate(BaseModel):
    source_type: str = Field(pattern="^(youtube|podcast|article|news|manual|search_console)$")
    url: str
    website_id: int | None = None
    title: str | None = None


class QuestionsCreate(BaseModel):
    questions: list[str] = Field(min_length=1)
    source_id: int | None = None


class FileSourceCreate(BaseModel):
    filename: str = Field(max_length=300)
    content: str = Field(max_length=2_000_000)
    website_id: int | None = None


@router.post("/sources")
def add_source(db: DbSession, payload: SourceCreate):
    return ResearchService(db).add_source(
        payload.source_type, payload.url, payload.website_id, payload.title
    )


@router.post("/sources/from-file")
def add_file_source(db: DbSession, payload: FileSourceCreate):
    """Local file opened or drag-and-dropped in the desktop app."""
    return ResearchService(db).add_file_source(payload.filename, payload.content, payload.website_id)


@router.get("/sources")
def list_sources(db: DbSession, pagination: PaginationDep, source_type: str | None = None):
    items, total = ResearchService(db).list_sources(pagination.page, pagination.page_size, source_type)
    return page_response(items, total, pagination)


@router.get("/sources/{source_id}")
def get_source(db: DbSession, source_id: int):
    source = ResearchService(db).get_source(source_id)
    if source is None:
        raise NotFoundError("research.source_not_found", f"Research source {source_id} does not exist")
    return source


@router.delete("/sources/{source_id}")
def delete_source(db: DbSession, source_id: int):
    if not ResearchService(db).delete_source(source_id):
        raise NotFoundError("research.source_not_found", f"Research source {source_id} does not exist")
    return {"deleted": source_id}


@router.get("/sources/{source_id}/gap")
def source_gap(db: DbSession, source_id: int):
    items = ResearchService(db).content_gap(source_id)
    return {"items": items, "total": len(items)}


@router.get("/questions")
def list_questions(db: DbSession, source_id: int | None = Query(default=None)):
    items = ResearchService(db).list_questions(source_id)
    return {"items": items, "total": len(items)}


@router.post("/questions")
def add_questions(db: DbSession, payload: QuestionsCreate):
    added = ResearchService(db).add_questions(payload.questions, payload.source_id)
    return {"added": added}


@router.post("/questions/{question_id}/answered")
def mark_answered(db: DbSession, question_id: int, answered: bool = True):
    ResearchService(db).set_question_answered(question_id, answered)
    return {"id": question_id, "answered": answered}
