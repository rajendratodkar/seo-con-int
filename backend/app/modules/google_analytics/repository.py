"""Google Analytics persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class GoogleAnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    # -- connections ---------------------------------------------------------------
    def upsert_connection(self, website_id: int, property_id: str, property_name: str | None) -> dict:
        self.db.execute(
            text(
                "INSERT INTO ga_connections (website_id, property_id, property_name) "
                "VALUES (:w, :p, :n) "
                "ON CONFLICT(website_id) DO UPDATE SET property_id = :p, property_name = :n, "
                "status = 'connected', updated_at = datetime('now')"
            ),
            {"w": website_id, "p": property_id, "n": property_name},
        )
        self.db.commit()
        return self.get_connection(website_id)

    def get_connection(self, website_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM ga_connections WHERE website_id = :w"), {"w": website_id}
        ).mappings().first()
        return dict(row) if row else None

    def delete_connection(self, website_id: int) -> None:
        self.db.execute(text("DELETE FROM ga_connections WHERE website_id = :w"), {"w": website_id})
        self.db.commit()

    # -- daily metrics ----------------------------------------------------------------
    def upsert_daily(self, website_id: int, rows: list[dict]) -> int:
        for row in rows:
            self.db.execute(
                text(
                    "INSERT INTO ga_metrics_daily (website_id, date, sessions, active_users, pageviews) "
                    "VALUES (:w, :d, :s, :u, :p) "
                    "ON CONFLICT(website_id, date) DO UPDATE SET sessions = :s, active_users = :u, pageviews = :p"
                ),
                {"w": website_id, "d": row["date"], "s": row["sessions"],
                 "u": row["active_users"], "p": row["pageviews"]},
            )
        self.db.commit()
        return len(rows)

    def range_totals(self, website_id: int, start: str, end: str) -> dict:
        row = self.db.execute(
            text(
                "SELECT COALESCE(SUM(sessions), 0) AS sessions, COALESCE(SUM(active_users), 0) AS active_users, "
                "COALESCE(SUM(pageviews), 0) AS pageviews, COUNT(*) AS days "
                "FROM ga_metrics_daily WHERE website_id = :w AND date >= :s AND date <= :e"
            ),
            {"w": website_id, "s": start, "e": end},
        ).mappings().one()
        return dict(row)

    def daily_series(self, website_id: int, start: str, end: str) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT date, sessions, active_users, pageviews FROM ga_metrics_daily "
                "WHERE website_id = :w AND date >= :s AND date <= :e ORDER BY date"
            ),
            {"w": website_id, "s": start, "e": end},
        ).mappings().all()
        return [dict(r) for r in rows]

    def last_date(self, website_id: int) -> str | None:
        return self.db.execute(
            text("SELECT MAX(date) FROM ga_metrics_daily WHERE website_id = :w"), {"w": website_id}
        ).scalar()
