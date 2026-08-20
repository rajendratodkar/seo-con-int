"""Data access for Search Console properties and metrics."""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session


class SearchConsoleRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- properties -----------------------------------------------------------

    def list_properties(self) -> list[dict]:
        rows = self.db.execute(text("SELECT * FROM search_console_properties ORDER BY id")).mappings().all()
        return [dict(r) for r in rows]

    def get_property(self, property_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM search_console_properties WHERE id = :id"), {"id": property_id}
        ).mappings().first()
        return dict(row) if row else None

    def upsert_property(self, site_url: str, website_id: int | None, permission_level: str | None, status: str) -> int:
        existing = self.db.execute(
            text("SELECT id FROM search_console_properties WHERE site_url = :url"), {"url": site_url}
        ).scalar_one_or_none()
        if existing:
            self.db.execute(
                text(
                    "UPDATE search_console_properties SET website_id=:website_id, permission_level=:perm, "
                    "status=:status, connected_at=CASE WHEN :status='connected' THEN datetime('now') ELSE connected_at END, "
                    "updated_at=datetime('now') WHERE id=:id"
                ),
                {"website_id": website_id, "perm": permission_level, "status": status, "id": existing},
            )
            self.db.commit()
            return existing
        result = self.db.execute(
            text(
                "INSERT INTO search_console_properties (website_id, site_url, permission_level, status) "
                "VALUES (:website_id, :url, :perm, :status)"
            ),
            {"website_id": website_id, "url": site_url, "perm": permission_level, "status": status},
        )
        self.db.commit()
        return result.lastrowid

    # --- data ------------------------------------------------------------------

    def store_raw(self, property_id: int, sync_log_id: int | None, request_dims: dict, payload: dict) -> None:
        self.db.execute(
            text(
                "INSERT INTO search_console_raw (property_id, sync_log_id, request_dims, payload) "
                "VALUES (:property_id, :sync_log_id, :request_dims, :payload)"
            ),
            {
                "property_id": property_id,
                "sync_log_id": sync_log_id,
                "request_dims": json.dumps(request_dims),
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )

    def upsert_rows(self, website_id: int, property_id: int, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            result = self.db.execute(
                text(
                    "INSERT INTO search_console_data "
                    "(website_id, property_id, date, query, page_url, clicks, impressions, ctr, position) "
                    "VALUES (:website_id, :property_id, :date, :query, :page_url, :clicks, :impressions, :ctr, :position) "
                    "ON CONFLICT (property_id, date, query, page_url, device, country) DO UPDATE SET "
                    "clicks=excluded.clicks, impressions=excluded.impressions, "
                    "ctr=excluded.ctr, position=excluded.position"
                ),
                {
                    "website_id": website_id, "property_id": property_id,
                    "date": row["date"], "query": row.get("query"), "page_url": row.get("page_url"),
                    "clicks": row["clicks"], "impressions": row["impressions"],
                    "ctr": row["ctr"], "position": row["position"],
                },
            )
            count += result.rowcount or 0
        return count

    def data_stats(self, website_id: int | None) -> dict:
        where = "WHERE website_id = :website_id" if website_id else ""
        params = {"website_id": website_id} if website_id else {}
        row = self.db.execute(
            text(
                f"SELECT COUNT(*) AS rows, MIN(date) AS first_date, MAX(date) AS last_date, "
                f"SUM(clicks) AS clicks, SUM(impressions) AS impressions FROM search_console_data {where}"
            ),
            params,
        ).mappings().first()
        return dict(row)
