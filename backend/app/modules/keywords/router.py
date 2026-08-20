"""Keywords module: track/import keywords, seed from Search Console queries."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.api.dependencies import DbSession, PaginationDep, page_response
from app.core.exceptions import ConflictError

router = APIRouter()


class KeywordCreate(BaseModel):
    website_id: int
    keyword: str = Field(min_length=2, max_length=200)
    search_intent: str | None = None
    group_name: str | None = None


@router.post("/")
def create(db: DbSession, payload: KeywordCreate):
    normalized = payload.keyword.strip().lower()
    row = db.execute(
        text("SELECT id FROM keywords WHERE website_id = :w AND normalized = :n"),
        {"w": payload.website_id, "n": normalized},
    ).first()
    if row:
        raise ConflictError("keyword.duplicate", f"Keyword already exists: {payload.keyword}")
    result = db.execute(
        text(
            "INSERT INTO keywords (website_id, keyword, normalized, search_intent, group_name, source) "
            "VALUES (:w, :k, :n, :i, :g, 'manual')"
        ),
        {"w": payload.website_id, "k": payload.keyword.strip(), "n": normalized,
         "i": payload.search_intent, "g": payload.group_name},
    )
    db.commit()
    return dict(db.execute(
        text("SELECT * FROM keywords WHERE id = :id"), {"id": result.lastrowid}
    ).mappings().first())


@router.post("/import-from-search-console")
def import_from_sc(db: DbSession, website_id: int = Query(...), min_impressions: int = Query(default=100)):
    """Top SC queries become tracked keywords (data-based, source='search_console')."""
    rows = db.execute(
        text(
            "SELECT query, SUM(impressions) AS impressions FROM search_console_data "
            "WHERE website_id = :w AND query IS NOT NULL AND date >= date('now', '-90 days') "
            "GROUP BY query HAVING impressions >= :min ORDER BY impressions DESC LIMIT 200"
        ),
        {"w": website_id, "min": min_impressions},
    ).mappings().all()
    added = 0
    for row in rows:
        normalized = row["query"].strip().lower()
        result = db.execute(
            text(
                "INSERT OR IGNORE INTO keywords (website_id, keyword, normalized, source) "
                "VALUES (:w, :k, :n, 'search_console')"
            ),
            {"w": website_id, "k": row["query"].strip(), "n": normalized},
        )
        added += result.rowcount
    db.commit()
    return {"added": added}


@router.get("/")
def list_keywords(db: DbSession, pagination: PaginationDep, website_id: int = Query(...)):
    rows = db.execute(
        text(
            "SELECT * FROM keywords WHERE website_id = :w ORDER BY id DESC LIMIT :limit OFFSET :offset"
        ),
        {"w": website_id, "limit": pagination.page_size, "offset": pagination.offset},
    ).mappings().all()
    total = db.execute(text("SELECT COUNT(*) FROM keywords WHERE website_id = :w"), {"w": website_id}).scalar()
    return page_response([dict(r) for r in rows], total, pagination)


@router.delete("/{keyword_id}")
def delete(db: DbSession, keyword_id: int):
    result = db.execute(text("DELETE FROM keywords WHERE id = :id"), {"id": keyword_id})
    db.commit()
    return {"deleted": keyword_id, "found": result.rowcount > 0}
