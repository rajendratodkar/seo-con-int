"""Content ideas persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class ContentIdeasRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, idea: dict) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO content_ideas (website_id, source_type, source_id, title, description, status, score) "
                "VALUES (:website_id, :source_type, :source_id, :title, :description, :status, :score)"
            ),
            idea,
        )
        self.db.commit()
        return result.lastrowid

    def get(self, idea_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM content_ideas WHERE id = :id"), {"id": idea_id}
        ).mappings().first()
        return dict(row) if row else None

    def list(self, page: int, page_size: int, website_id: int | None, status: str | None) -> tuple[list[dict], int]:
        clauses, params = [], {"limit": page_size, "offset": (page - 1) * page_size}
        if website_id:
            clauses.append("website_id = :website_id")
            params["website_id"] = website_id
        if status:
            clauses.append("status = :status")
            params["status"] = status
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.db.execute(
            text("SELECT * FROM content_ideas " + where + " ORDER BY score DESC NULLS LAST, id DESC LIMIT :limit OFFSET :offset"),
            params,
        ).mappings().all()
        total = self.db.execute(text("SELECT COUNT(*) FROM content_ideas " + where), params).scalar()
        return [dict(r) for r in rows], total

    def update_status(self, idea_id: int, status: str) -> None:
        self.db.execute(
            text("UPDATE content_ideas SET status = :status, updated_at = datetime('now') WHERE id = :id"),
            {"id": idea_id, "status": status},
        )
        self.db.commit()

    def update_score(self, idea_id: int, score: float) -> None:
        self.db.execute(
            text("UPDATE content_ideas SET score = :score, updated_at = datetime('now') WHERE id = :id"),
            {"id": idea_id, "score": score},
        )
        self.db.commit()

    def delete(self, idea_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM content_ideas WHERE id = :id"), {"id": idea_id})
        self.db.commit()
        return result.rowcount > 0

    def title_exists(self, title: str, exclude_id: int | None = None) -> bool:
        row = self.db.execute(
            text("SELECT id FROM content_ideas WHERE LOWER(title) = LOWER(:title) AND id != :exclude_id"),
            {"title": title.strip(), "exclude_id": exclude_id or -1},
        ).first()
        return row is not None
