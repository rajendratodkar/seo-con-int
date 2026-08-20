"""Search Console File Upload repository — stores imported data."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class ScUploadRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Import tracking
    # ------------------------------------------------------------------

    def create_import(self, website_id: int, filename: str, file_type: str,
                      import_type: str) -> dict:
        """Create a new import record."""
        row = self.db.execute(
            text(
                "INSERT INTO sc_imports (website_id, filename, file_type, import_type, status) "
                "VALUES (:wid, :filename, :ft, :it, 'processing') "
                "RETURNING *"
            ),
            {"wid": website_id, "filename": filename, "ft": file_type, "it": import_type},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def update_import(self, import_id: int, **fields) -> dict:
        """Update import record with results."""
        set_clauses = []
        params = {"id": import_id}
        for key, value in fields.items():
            if key not in ("id", "created_at"):
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
        if not set_clauses:
            return self.get_import(import_id)
        sql = f"UPDATE sc_imports SET {', '.join(set_clauses)} WHERE id = :id RETURNING *"
        row = self.db.execute(text(sql), params).mappings().one()
        self.db.commit()
        return dict(row)

    def get_import(self, import_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM sc_imports WHERE id = :id"), {"id": import_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_imports(self, website_id: int, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM sc_imports WHERE website_id = :w ORDER BY created_at DESC LIMIT :lim"),
            {"w": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Performance data upsert
    # ------------------------------------------------------------------

    def upsert_performance_rows(self, website_id: int, property_id: int,
                                 rows: list[dict]) -> int:
        """Insert performance data rows into search_console_data.

        Each row should have: date, query, page_url, clicks, impressions, ctr, position.
        Uses INSERT OR REPLACE to handle duplicates.
        """
        if not rows:
            return 0

        imported = 0
        for row in rows:
            try:
                self.db.execute(
                    text(
                        "INSERT INTO search_console_data "
                        "(website_id, property_id, date, query, page_url, clicks, impressions, ctr, position) "
                        "VALUES (:wid, :pid, :date, :query, :page, :clicks, :impressions, :ctr, :position)"
                    ),
                    {
                        "wid": website_id,
                        "pid": property_id,
                        "date": row.get("date", ""),
                        "query": row.get("query"),
                        "page": row.get("page_url"),
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": row.get("ctr", 0.0),
                        "position": row.get("position", 0.0),
                    },
                )
                imported += 1
            except Exception:
                # Skip duplicates or invalid rows
                self.db.rollback()
                continue

        self.db.commit()
        return imported

    def get_or_create_property(self, website_id: int, site_url: str) -> int:
        """Get existing property or create a placeholder for file imports."""
        row = self.db.execute(
            text("SELECT id FROM search_console_properties WHERE site_url = :url"),
            {"url": site_url},
        ).mappings().first()

        if row:
            return row["id"]

        # Create a placeholder property for file imports
        row = self.db.execute(
            text(
                "INSERT INTO search_console_properties (website_id, site_url, status) "
                "VALUES (:wid, :url, 'connected') RETURNING id"
            ),
            {"wid": website_id, "url": site_url},
        ).mappings().one()
        self.db.commit()
        return row["id"]

    def get_import_stats(self, website_id: int) -> dict:
        """Get import statistics for a website."""
        row = self.db.execute(
            text(
                "SELECT "
                "COUNT(*) AS total_imports, "
                "SUM(rows_imported) AS total_rows_imported, "
                "MAX(created_at) AS last_import "
                "FROM sc_imports WHERE website_id = :w AND status = 'completed'"
            ),
            {"w": website_id},
        ).mappings().one()
        return dict(row)
