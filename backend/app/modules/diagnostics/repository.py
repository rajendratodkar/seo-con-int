"""Diagnostics repository — usage events live in SQLite (Rule: SQL only here)."""
from sqlalchemy import text
from sqlalchemy.orm import Session

MAX_EVENTS = 5000  # hard cap so analytics never eats disk space


class DiagnosticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def insert_event(self, event: str, detail: str | None) -> None:
        self.db.execute(
            text("INSERT INTO usage_events (event, detail) VALUES (:event, :detail)"),
            {"event": event, "detail": detail},
        )
        self.db.commit()
        self._enforce_cap()

    def list_events(self, limit: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT id, event, detail, created_at FROM usage_events "
                "ORDER BY id DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def counts(self) -> dict:
        row = self.db.execute(
            text("SELECT COUNT(*) AS total, SUM(event = 'crash') AS crashes FROM usage_events")
        ).mappings().first()
        return {"total": row["total"] or 0, "crashes": row["crashes"] or 0}

    def _enforce_cap(self) -> None:
        self.db.execute(
            text(
                "DELETE FROM usage_events WHERE id NOT IN "
                "(SELECT id FROM usage_events ORDER BY id DESC LIMIT :keep)"
            ),
            {"keep": MAX_EVENTS},
        )
        self.db.commit()
