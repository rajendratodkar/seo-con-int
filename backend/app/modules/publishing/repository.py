"""Publishing history persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class PublishingRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, draft_id: int, target: str, action: str, status: str,
            remote_id: str | None = None, remote_url: str | None = None,
            response_path: str | None = None, error: str | None = None) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO publish_logs (draft_id, target, action, status, remote_id, remote_url, response_path, error) "
                "VALUES (:d, :t, :a, :s, :rid, :rurl, :rpath, :err)"
            ),
            {"d": draft_id, "t": target, "a": action, "s": status,
             "rid": remote_id, "rurl": remote_url, "rpath": response_path, "err": error},
        )
        self.db.commit()
        return result.lastrowid

    def list_logs(self, draft_id: int | None = None, limit: int = 50) -> list[dict]:
        query = "SELECT * FROM publish_logs"
        params: dict = {"limit": limit}
        if draft_id is not None:
            query += " WHERE draft_id = :draft_id"
            params["draft_id"] = draft_id
        query += " ORDER BY id DESC LIMIT :limit"
        rows = self.db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def draft_with_plan(self, draft_id: int) -> dict | None:
        """Draft row joined with its plan title (needed for post titles/filenames)."""
        row = self.db.execute(
            text(
                "SELECT d.*, p.title AS plan_title, p.search_intent "
                "FROM article_drafts d JOIN article_plans p ON p.id = d.plan_id "
                "WHERE d.id = :id"
            ),
            {"id": draft_id},
        ).mappings().first()
        return dict(row) if row else None
