"""Database queries for content calendar."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class CalendarRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_table(self) -> None:
        """Create the calendar_events table if it doesn't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS calendar_events ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE, "
            "title TEXT NOT NULL, "
            "description TEXT, "
            "event_type TEXT NOT NULL DEFAULT 'article', "
            "status TEXT NOT NULL DEFAULT 'planned', "
            "start_date TEXT NOT NULL, "
            "end_date TEXT, "
            "plan_id INTEGER REFERENCES article_plans(id) ON DELETE SET NULL, "
            "draft_id INTEGER REFERENCES article_drafts(id) ON DELETE SET NULL, "
            "priority TEXT NOT NULL DEFAULT 'normal', "
            "color TEXT, "
            "assignee TEXT, "
            "notes TEXT, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_calendar_events_website ON calendar_events(website_id)"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_calendar_events_dates ON calendar_events(start_date, end_date)"
        ))
        self.db.commit()

    def create_event(self, data: dict) -> dict:
        fields = {k: v for k, v in data.items() if v is not None}
        cols = ", ".join(fields.keys())
        placeholders = ", ".join(f":{k}" for k in fields.keys())
        row = self.db.execute(
            text(f"INSERT INTO calendar_events ({cols}) VALUES ({placeholders}) RETURNING *"),
            fields,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_event(self, event_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM calendar_events WHERE id = :id"), {"id": event_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_events(
        self, website_id: int, start_date: str | None = None, end_date: str | None = None,
        status: str | None = None, event_type: str | None = None,
    ) -> list[dict]:
        conditions = ["website_id = :wid"]
        params: dict = {"wid": website_id}
        if start_date:
            conditions.append("(start_date >= :start OR (end_date IS NOT NULL AND end_date >= :start))")
            params["start"] = start_date
        if end_date:
            conditions.append("(start_date <= :end OR end_date IS NULL)")
            params["end"] = end_date
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if event_type:
            conditions.append("event_type = :etype")
            params["etype"] = event_type
        where = " AND ".join(conditions)
        rows = self.db.execute(
            text(f"SELECT * FROM calendar_events WHERE {where} ORDER BY start_date ASC"),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_event(self, event_id: int, **fields) -> dict | None:
        sets, params = [], {"id": event_id}
        for k, v in fields.items():
            if v is not None:
                sets.append(f"{k} = :{k}")
                params[k] = v
        if not sets:
            return self.get_event(event_id)
        sets.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE calendar_events SET {', '.join(sets)} WHERE id = :id RETURNING *"), params
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_event(self, event_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM calendar_events WHERE id = :id"), {"id": event_id}
        )
        self.db.commit()
        return result.rowcount > 0

    def pipeline_summary(self, website_id: int) -> dict:
        """Get count of events by status for pipeline view."""
        rows = self.db.execute(
            text(
                "SELECT status, COUNT(*) AS n FROM calendar_events "
                "WHERE website_id = :wid GROUP BY status"
            ),
            {"wid": website_id},
        ).mappings().all()
        return {r.status: r.n for r in rows}

    def upcoming_deadlines(self, website_id: int, days: int = 14) -> list[dict]:
        """Get events with deadlines in the next N days."""
        rows = self.db.execute(
            text(
                "SELECT * FROM calendar_events WHERE website_id = :wid "
                "AND start_date <= date('now', :days) AND status NOT IN ('published', 'cancelled') "
                "ORDER BY start_date ASC LIMIT 20"
            ),
            {"wid": website_id, "days": f"+{days} days"},
        ).mappings().all()
        return [dict(r) for r in rows]
