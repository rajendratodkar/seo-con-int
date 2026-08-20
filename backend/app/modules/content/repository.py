"""Article drafts persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class DraftsRepository:
    def __init__(self, db: Session):
        self.db = db

    def next_version(self, plan_id: int) -> int:
        row = self.db.execute(
            text("SELECT COALESCE(MAX(version), 0) FROM article_drafts WHERE plan_id = :p"), {"p": plan_id}
        ).scalar()
        return row + 1

    def create(self, plan_id: int, version: int, content: str, content_path: str | None,
               ai_provider: str | None, ai_model: str | None) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO article_drafts (plan_id, version, content, content_path, ai_provider, ai_model, status) "
                "VALUES (:p, :v, :c, :path, :provider, :model, 'ai_suggestion')"
            ),
            {"p": plan_id, "v": version, "c": content, "path": content_path,
             "provider": ai_provider, "model": ai_model},
        )
        self.db.commit()
        return result.lastrowid

    def get(self, draft_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM article_drafts WHERE id = :id"), {"id": draft_id}
        ).mappings().first()
        return dict(row) if row else None

    def list_for_plan(self, plan_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT id, plan_id, version, content_path, ai_provider, ai_model, status, created_at "
                 "FROM article_drafts WHERE plan_id = :p ORDER BY version DESC"),
            {"p": plan_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def list_all(self, status: str | None = None) -> list[dict]:
        query = (
            "SELECT d.id, d.plan_id, d.version, d.status, d.ai_provider, d.created_at, p.title AS plan_title "
            "FROM article_drafts d JOIN article_plans p ON p.id = d.plan_id"
        )
        params: dict = {}
        if status:
            query += " WHERE d.status = :status"
            params["status"] = status
        query += " ORDER BY d.id DESC"
        rows = self.db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def update(self, draft_id: int, content: str, status: str) -> None:
        self.db.execute(
            text("UPDATE article_drafts SET content = :c, status = :s WHERE id = :id"),
            {"id": draft_id, "c": content, "s": status},
        )
        self.db.commit()
