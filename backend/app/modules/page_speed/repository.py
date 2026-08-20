"""Database queries for page speed insights."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class PageSpeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_table(self) -> None:
        """Create the page_speed_snapshots table if it doesn't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS page_speed_snapshots ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE, "
            "page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE, "
            "url TEXT NOT NULL, "
            "lcp REAL, fid REAL, cls REAL, fcp REAL, ttfb REAL, tti REAL, "
            "performance_score INTEGER, accessibility_score INTEGER, "
            "best_practices_score INTEGER, seo_score INTEGER, "
            "opportunities TEXT, diagnostics TEXT, "
            "source TEXT NOT NULL DEFAULT 'manual', "
            "checked_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_page_speed_page ON page_speed_snapshots(page_id)"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_page_speed_website ON page_speed_snapshots(website_id)"
        ))
        self.db.commit()

    def save_snapshot(self, data: dict) -> dict:
        # Serialize JSON fields
        if "opportunities" in data and isinstance(data["opportunities"], list):
            data["opportunities"] = json.dumps(data["opportunities"])
        if "diagnostics" in data and isinstance(data["diagnostics"], list):
            data["diagnostics"] = json.dumps(data["diagnostics"])
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        row = self.db.execute(
            text(f"INSERT INTO page_speed_snapshots ({cols}) VALUES ({placeholders}) RETURNING *"),
            data,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_latest(self, page_id: int) -> dict | None:
        row = self.db.execute(
            text(
                "SELECT * FROM page_speed_snapshots WHERE page_id = :pid "
                "ORDER BY checked_at DESC LIMIT 1"
            ),
            {"pid": page_id},
        ).mappings().one_or_none()
        return self._deserialize(row) if row else None

    def get_history(self, page_id: int, limit: int = 30) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM page_speed_snapshots WHERE page_id = :pid "
                "ORDER BY checked_at DESC LIMIT :lim"
            ),
            {"pid": page_id, "lim": limit},
        ).mappings().all()
        return [self._deserialize(r) for r in rows]

    def get_website_summary(self, website_id: int) -> dict:
        """Get average scores across all pages for a website."""
        row = self.db.execute(
            text(
                "SELECT "
                "COUNT(DISTINCT page_id) AS pages_checked, "
                "ROUND(AVG(performance_score), 0) AS avg_performance, "
                "ROUND(AVG(accessibility_score), 0) AS avg_accessibility, "
                "ROUND(AVG(best_practices_score), 0) AS avg_best_practices, "
                "ROUND(AVG(seo_score), 0) AS avg_seo, "
                "ROUND(AVG(lcp), 2) AS avg_lcp, "
                "ROUND(AVG(fid), 1) AS avg_fid, "
                "ROUND(AVG(cls), 3) AS avg_cls, "
                "ROUND(AVG(fcp), 2) AS avg_fcp, "
                "ROUND(AVG(ttfb), 2) AS avg_ttfb "
                "FROM page_speed_snapshots WHERE website_id = :wid "
                "AND checked_at >= datetime('now', '-30 days')"
            ),
            {"wid": website_id},
        ).mappings().one()
        return dict(row)

    def get_pagescores(self, website_id: int, limit: int = 50) -> list[dict]:
        """Get latest score per page for the website."""
        rows = self.db.execute(
            text(
                "SELECT pss.* FROM page_speed_snapshots pss "
                "INNER JOIN ("
                "  SELECT page_id, MAX(checked_at) AS max_checked "
                "  FROM page_speed_snapshots WHERE website_id = :wid "
                "  GROUP BY page_id"
                ") latest ON pss.page_id = latest.page_id AND pss.checked_at = latest.max_checked "
                "ORDER BY pss.performance_score ASC LIMIT :lim"
            ),
            {"wid": website_id, "lim": limit},
        ).mappings().all()
        return [self._deserialize(r) for r in rows]

    @staticmethod
    def _deserialize(row) -> dict:
        d = dict(row)
        for key in ("opportunities", "diagnostics"):
            if isinstance(d.get(key), str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = []
        return d
