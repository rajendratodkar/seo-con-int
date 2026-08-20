"""Discussion persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class DiscussionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, topic: str, website_id: int | None, idea_id: int | None) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO discussions (website_id, idea_id, topic) VALUES (:w, :i, :t)"
            ),
            {"w": website_id, "i": idea_id, "t": topic},
        )
        self.db.commit()
        return result.lastrowid

    def get(self, discussion_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM discussions WHERE id = :id"), {"id": discussion_id}
        ).mappings().first()
        return dict(row) if row else None

    def list(self, page: int, page_size: int) -> tuple[list[dict], int]:
        rows = self.db.execute(
            text("SELECT * FROM discussions ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()
        total = self.db.execute(text("SELECT COUNT(*) FROM discussions")).scalar()
        return [dict(r) for r in rows], total

    def set_status(self, discussion_id: int, status: str) -> None:
        self.db.execute(
            text("UPDATE discussions SET status = :s, updated_at = datetime('now') WHERE id = :id"),
            {"id": discussion_id, "s": status},
        )
        self.db.commit()

    def add_message(self, discussion_id: int, role: str, content: str, provider: str | None) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO discussion_messages (discussion_id, role, content, provider) "
                "VALUES (:d, :r, :c, :p)"
            ),
            {"d": discussion_id, "r": role, "c": content, "p": provider},
        )
        self.db.execute(
            text("UPDATE discussions SET updated_at = datetime('now') WHERE id = :id"),
            {"id": discussion_id},
        )
        self.db.commit()
        return result.lastrowid

    def list_messages(self, discussion_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM discussion_messages WHERE discussion_id = :d ORDER BY id"),
            {"d": discussion_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def add_decision(self, discussion_id: int, decision: str, rationale: str | None) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO discussion_decisions (discussion_id, decision, rationale) "
                "VALUES (:d, :dec, :r)"
            ),
            {"d": discussion_id, "dec": decision, "r": rationale},
        )
        self.db.execute(
            text("UPDATE discussions SET status = 'decided', updated_at = datetime('now') WHERE id = :id"),
            {"id": discussion_id},
        )
        self.db.commit()
        return result.lastrowid

    def list_decisions(self, discussion_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM discussion_decisions WHERE discussion_id = :d ORDER BY id"),
            {"d": discussion_id},
        ).mappings().all()
        return [dict(r) for r in rows]
