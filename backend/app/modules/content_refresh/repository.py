"""Content Refresh repository — storage and retrieval."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError


class ContentRefreshRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Rules CRUD
    # ------------------------------------------------------------------

    def create_rule(self, website_id: int, name: str, min_age_days: int,
                    traffic_drop_pct: float, staleness_weight: float, traffic_weight: float) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO refresh_rules (website_id, name, min_age_days, traffic_drop_pct, staleness_weight, traffic_weight) "
                "VALUES (:wid, :name, :age, :drop, :sw, :tw) RETURNING *"
            ),
            {"wid": website_id, "name": name, "age": min_age_days, "drop": traffic_drop_pct,
             "sw": staleness_weight, "tw": traffic_weight},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_rule(self, rule_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM refresh_rules WHERE id = :id"), {"id": rule_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_rules(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM refresh_rules WHERE website_id = :w ORDER BY created_at DESC"),
            {"w": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_rule(self, rule_id: int, fields: dict) -> dict:
        set_clauses = []
        params = {"id": rule_id}
        for key, value in fields.items():
            if value is not None and key not in ("id", "created_at", "website_id"):
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
        if not set_clauses:
            return self.get_rule(rule_id) or {}
        set_clauses.append("updated_at = datetime('now')")
        sql = f"UPDATE refresh_rules SET {', '.join(set_clauses)} WHERE id = :id RETURNING *"
        row = self.db.execute(text(sql), params).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_rule(self, rule_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM refresh_rules WHERE id = :id"), {"id": rule_id})
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Schedules CRUD
    # ------------------------------------------------------------------

    def upsert_schedule(self, website_id: int, page_id: int, rule_id: int | None,
                        priority_score: float, priority_date: str, reason: str,
                        suggested_changes: list[dict]) -> dict:
        """Create or update a schedule entry for a page."""
        existing = self.db.execute(
            text("SELECT id FROM refresh_schedules WHERE page_id = :pid AND status = 'pending'"),
            {"pid": page_id},
        ).mappings().first()

        if existing:
            row = self.db.execute(
                text(
                    "UPDATE refresh_schedules SET priority_score = :score, priority_date = :date, "
                    "reason = :reason, suggested_changes = :changes, rule_id = :rid, updated_at = datetime('now') "
                    "WHERE id = :id RETURNING *"
                ),
                {"score": priority_score, "date": priority_date, "reason": reason,
                 "changes": json.dumps(suggested_changes), "rid": rule_id, "id": existing["id"]},
            ).mappings().one()
        else:
            row = self.db.execute(
                text(
                    "INSERT INTO refresh_schedules (website_id, page_id, rule_id, priority_score, priority_date, reason, suggested_changes) "
                    "VALUES (:wid, :pid, :rid, :score, :date, :reason, :changes) RETURNING *"
                ),
                {"wid": website_id, "pid": page_id, "rid": rule_id, "score": priority_score,
                 "date": priority_date, "reason": reason, "changes": json.dumps(suggested_changes)},
            ).mappings().one()

        self.db.commit()
        return dict(row)

    def list_schedules(self, website_id: int, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM refresh_schedules WHERE website_id = :w"
        params = {"w": website_id}
        if status:
            query += " AND status = :status"
            params["status"] = status
        query += " ORDER BY priority_score DESC"
        rows = self.db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def get_schedule(self, schedule_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM refresh_schedules WHERE id = :id"), {"id": schedule_id},
        ).mappings().first()
        return dict(row) if row else None

    def update_schedule_status(self, schedule_id: int, status: str) -> dict:
        row = self.db.execute(
            text("UPDATE refresh_schedules SET status = :s, updated_at = datetime('now') WHERE id = :id RETURNING *"),
            {"s": status, "id": schedule_id},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_schedule(self, schedule_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM refresh_schedules WHERE id = :id"), {"id": schedule_id},
        )
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def add_history(self, schedule_id: int, page_id: int, action: str,
                    changes_made: str | None = None, **metrics) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO refresh_history "
                "(schedule_id, page_id, action, changes_made, clicks_before, clicks_after, "
                "impressions_before, impressions_after, position_before, position_after, notes) "
                "VALUES (:sid, :pid, :action, :changes, :cb, :ca, :ib, :ia, :pb, :pa, :notes) RETURNING *"
            ),
            {
                "sid": schedule_id, "pid": page_id, "action": action, "changes": changes_made,
                "cb": metrics.get("clicks_before"), "ca": metrics.get("clicks_after"),
                "ib": metrics.get("impressions_before"), "ia": metrics.get("impressions_after"),
                "pb": metrics.get("position_before"), "pa": metrics.get("position_after"),
                "notes": metrics.get("notes"),
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def list_history(self, website_id: int, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT h.* FROM refresh_history h "
                "JOIN refresh_schedules s ON h.schedule_id = s.id "
                "WHERE s.website_id = :w ORDER BY h.created_at DESC LIMIT :lim"
            ),
            {"w": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, website_id: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT "
                "COUNT(*) AS total_schedules, "
                "SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending, "
                "SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress, "
                "SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed, "
                "SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) AS skipped, "
                "COALESCE(AVG(CASE WHEN status = 'pending' THEN priority_score END), 0) AS avg_priority "
                "FROM refresh_schedules WHERE website_id = :w"
            ),
            {"w": website_id},
        ).mappings().one()
        return dict(row)
