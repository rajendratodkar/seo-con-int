"""References & rules HTTP layer — official documents, never mixed with rules."""
from fastapi import APIRouter, Query
from sqlalchemy import text

from app.api.dependencies import DbSession

router = APIRouter()


@router.get("/")
def list_references(db: DbSession, category: str | None = Query(None)):
    if category:
        rows = db.execute(
            text("SELECT * FROM reference_docs WHERE category = :category ORDER BY category, title"),
            {"category": category},
        ).mappings().all()
    else:
        rows = db.execute(text("SELECT * FROM reference_docs ORDER BY category, title")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/categories")
def list_categories(db: DbSession):
    rows = db.execute(
        text("SELECT category, COUNT(*) AS count FROM reference_docs GROUP BY category ORDER BY category")
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/rules")
def list_rules(db: DbSession, category: str | None = Query(None), enabled: bool | None = Query(None)):
    query = (
        "SELECT sr.*, rd.title AS reference_title, rd.url AS reference_url "
        "FROM seo_rules sr LEFT JOIN reference_docs rd ON rd.id = sr.reference_id"
    )
    clauses, params = [], {}
    if category:
        clauses.append("sr.category = :category")
        params["category"] = category
    if enabled is not None:
        clauses.append("sr.enabled = :enabled")
        params["enabled"] = 1 if enabled else 0
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY sr.rule_code"
    rows = db.execute(text(query), params).mappings().all()
    return {"items": [dict(r) for r in rows]}
