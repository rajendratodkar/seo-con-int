"""Data access for websites — SQL only, no business decisions."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class WebsiteRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, offset: int, limit: int) -> tuple[list[dict], int]:
        rows = self.db.execute(
            text("SELECT * FROM websites ORDER BY id DESC LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset},
        ).mappings().all()
        total = self.db.execute(text("SELECT COUNT(*) AS c FROM websites")).scalar_one()
        return [dict(r) for r in rows], total

    def get(self, website_id: int) -> dict | None:
        row = self.db.execute(text("SELECT * FROM websites WHERE id = :id"), {"id": website_id}).mappings().first()
        return dict(row) if row else None

    def get_by_url(self, url: str) -> dict | None:
        row = self.db.execute(text("SELECT * FROM websites WHERE url = :url"), {"url": url}).mappings().first()
        return dict(row) if row else None

    def create(self, name: str, url: str, sitemap_url: str | None) -> dict:
        result = self.db.execute(
            text("INSERT INTO websites (name, url, sitemap_url) VALUES (:name, :url, :sitemap_url)"),
            {"name": name, "url": url, "sitemap_url": sitemap_url},
        )
        self.db.commit()
        return self.get(result.lastrowid)

    def update(self, website_id: int, fields: dict) -> dict | None:
        if not fields:
            return self.get(website_id)
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        fields["id"] = website_id
        self.db.execute(text(f"UPDATE websites SET {sets}, updated_at = datetime('now') WHERE id = :id"), fields)
        self.db.commit()
        return self.get(website_id)

    def delete(self, website_id: int) -> None:
        self.db.execute(text("DELETE FROM websites WHERE id = :id"), {"id": website_id})
        self.db.commit()
