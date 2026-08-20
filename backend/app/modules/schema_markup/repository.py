"""Database queries for schema markup storage.

Uses a new `page_schemas` table to store generated/validated JSON-LD per page.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


class SchemaRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_table(self) -> None:
        """Create the page_schemas table if it doesn't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS page_schemas ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE, "
            "schema_type TEXT NOT NULL, "
            "json_ld TEXT NOT NULL, "
            "validation_errors TEXT, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_page_schemas_page ON page_schemas(page_id)"
        ))
        self.db.commit()

    def save_schema(
        self, page_id: int, schema_type: str, json_ld: str, validation_errors: str | None = None,
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO page_schemas (page_id, schema_type, json_ld, validation_errors) "
                "VALUES (:pid, :stype, :jl, :ve) RETURNING *"
            ),
            {"pid": page_id, "stype": schema_type, "jl": json_ld, "ve": validation_errors},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def list_schemas_for_page(self, page_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM page_schemas WHERE page_id = :pid ORDER BY created_at DESC"),
            {"pid": page_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_schema(self, schema_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM page_schemas WHERE id = :id"), {"id": schema_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def delete_schema(self, schema_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM page_schemas WHERE id = :id"), {"id": schema_id}
        )
        self.db.commit()
        return result.rowcount > 0

    def get_page_schemas_summary(self, website_id: int) -> dict:
        """Count pages with/without schemas."""
        total = self.db.execute(
            text("SELECT COUNT(*) FROM pages WHERE website_id = :wid"), {"wid": website_id}
        ).scalar()
        with_schema = self.db.execute(
            text(
                "SELECT COUNT(DISTINCT ps.page_id) FROM page_schemas ps "
                "JOIN pages p ON p.id = ps.page_id WHERE p.website_id = :wid"
            ),
            {"wid": website_id},
        ).scalar()
        return {
            "total_pages": total,
            "pages_with_schema": with_schema,
            "pages_without_schema": total - with_schema,
            "coverage_pct": round((with_schema / total * 100) if total > 0 else 0, 1),
        }
