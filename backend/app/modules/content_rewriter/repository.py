"""Database queries for content rewriter."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class RewriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_table(self) -> None:
        """Create the rewrite_requests table if it doesn't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS rewrite_requests ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER REFERENCES websites(id) ON DELETE SET NULL, "
            "page_id INTEGER REFERENCES pages(id) ON DELETE SET NULL, "
            "content_type TEXT NOT NULL, "
            "original_text TEXT NOT NULL, "
            "context TEXT, "
            "provider TEXT, "
            "model TEXT, "
            "rewrites TEXT NOT NULL DEFAULT '[]', "
            "selected_index INTEGER, "
            "applied INTEGER NOT NULL DEFAULT 0, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_rewrite_requests_website ON rewrite_requests(website_id)"
        ))
        self.db.commit()

    def save(self, data: dict) -> dict:
        if "rewrites" in data and isinstance(data["rewrites"], list):
            data["rewrites"] = json.dumps(data["rewrites"])
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        row = self.db.execute(
            text(f"INSERT INTO rewrite_requests ({cols}) VALUES ({placeholders}) RETURNING *"),
            data,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get(self, request_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM rewrite_requests WHERE id = :id"), {"id": request_id}
        ).mappings().one_or_none()
        return self._deserialize(row) if row else None

    def list_recent(self, website_id: int | None = None, limit: int = 50) -> list[dict]:
        if website_id:
            rows = self.db.execute(
                text(
                    "SELECT * FROM rewrite_requests WHERE website_id = :wid "
                    "ORDER BY created_at DESC LIMIT :lim"
                ),
                {"wid": website_id, "lim": limit},
            ).mappings().all()
        else:
            rows = self.db.execute(
                text("SELECT * FROM rewrite_requests ORDER BY created_at DESC LIMIT :lim"),
                {"lim": limit},
            ).mappings().all()
        return [self._deserialize(r) for r in rows]

    def select_rewrite(self, request_id: int, selected_index: int) -> dict | None:
        row = self.db.execute(
            text(
                "UPDATE rewrite_requests SET selected_index = :idx WHERE id = :id RETURNING *"
            ),
            {"id": request_id, "idx": selected_index},
        ).mappings().one_or_none()
        self.db.commit()
        return self._deserialize(row) if row else None

    def mark_applied(self, request_id: int) -> dict | None:
        row = self.db.execute(
            text("UPDATE rewrite_requests SET applied = 1 WHERE id = :id RETURNING *"),
            {"id": request_id},
        ).mappings().one_or_none()
        self.db.commit()
        return self._deserialize(row) if row else None

    @staticmethod
    def _deserialize(row) -> dict:
        d = dict(row)
        if isinstance(d.get("rewrites"), str):
            try:
                d["rewrites"] = json.loads(d["rewrites"])
            except (json.JSONDecodeError, TypeError):
                d["rewrites"] = []
        d["applied"] = bool(d.get("applied", 0))
        return d
