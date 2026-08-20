"""SERP Preview repository — fetch page metadata for previews."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class SERPPreviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_page_meta(self, page_id: int) -> dict | None:
        """Get page metadata for SERP preview."""
        row = self.db.execute(
            text(
                "SELECT id, url, title, meta_description "
                "FROM pages WHERE id = :id"
            ),
            {"id": page_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_pages_for_website(self, website_id: int, limit: int = 50) -> list[dict]:
        """Get pages with metadata for bulk preview."""
        rows = self.db.execute(
            text(
                "SELECT id, url, title, meta_description "
                "FROM pages WHERE website_id = :wid "
                "AND (title IS NOT NULL OR meta_description IS NOT NULL) "
                "ORDER BY id DESC LIMIT :lim"
            ),
            {"wid": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_website_info(self, website_id: int) -> dict | None:
        """Get website name for SERP display."""
        row = self.db.execute(
            text("SELECT id, name, url FROM websites WHERE id = :id"),
            {"id": website_id},
        ).mappings().first()
        return dict(row) if row else None

    def update_page_meta(self, page_id: int, title: str | None = None, meta_description: str | None = None) -> dict | None:
        """Update page title and/or meta description."""
        updates = []
        params = {"id": page_id}

        if title is not None:
            updates.append("title = :title")
            params["title"] = title
        if meta_description is not None:
            updates.append("meta_description = :desc")
            params["desc"] = meta_description

        if not updates:
            return self.get_page_meta(page_id)

        updates.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE pages SET {', '.join(updates)} WHERE id = :id RETURNING id, url, title, meta_description"),
            params,
        ).mappings().first()
        self.db.commit()
        return dict(row) if row else None
