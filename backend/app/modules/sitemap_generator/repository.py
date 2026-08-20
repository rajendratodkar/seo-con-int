"""Database queries for sitemap generator."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class SitemapRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_tables(self) -> None:
        """Create sitemap tables if they don't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS sitemap_settings ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL UNIQUE REFERENCES websites(id) ON DELETE CASCADE, "
            "default_priority REAL NOT NULL DEFAULT 0.5, "
            "default_changefreq TEXT NOT NULL DEFAULT 'weekly', "
            "include_images INTEGER NOT NULL DEFAULT 1, "
            "include_news INTEGER NOT NULL DEFAULT 0, "
            "max_urls INTEGER NOT NULL DEFAULT 50000, "
            "exclude_patterns TEXT, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS sitemap_url_overrides ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE, "
            "url_pattern TEXT NOT NULL, "
            "priority REAL, "
            "changefreq TEXT, "
            "include INTEGER NOT NULL DEFAULT 1, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "UNIQUE (website_id, url_pattern))"
        ))
        self.db.commit()

    # --- Settings -------------------------------------------------------------

    def get_settings(self, website_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM sitemap_settings WHERE website_id = :wid"),
            {"wid": website_id},
        ).mappings().one_or_none()
        if not row:
            return None
        d = dict(row)
        if isinstance(d.get("exclude_patterns"), str):
            try:
                d["exclude_patterns"] = json.loads(d["exclude_patterns"])
            except (json.JSONDecodeError, TypeError):
                d["exclude_patterns"] = []
        return d

    def upsert_settings(self, website_id: int, **fields) -> dict:
        existing = self.get_settings(website_id)
        if "exclude_patterns" in fields and isinstance(fields["exclude_patterns"], list):
            fields["exclude_patterns"] = json.dumps(fields["exclude_patterns"])
        if existing:
            sets, params = [], {"wid": website_id}
            for k, v in fields.items():
                if v is not None:
                    sets.append(f"{k} = :{k}")
                    params[k] = v
            if sets:
                sets.append("updated_at = datetime('now')")
                self.db.execute(
                    text(f"UPDATE sitemap_settings SET {', '.join(sets)} WHERE website_id = :wid"), params
                )
                self.db.commit()
        else:
            fields["website_id"] = website_id
            cols = ", ".join(fields.keys())
            placeholders = ", ".join(f":{k}" for k in fields.keys())
            self.db.execute(
                text(f"INSERT INTO sitemap_settings ({cols}) VALUES ({placeholders})"), fields
            )
            self.db.commit()
        return self.get_settings(website_id) or {}

    # --- Overrides ------------------------------------------------------------

    def list_overrides(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM sitemap_url_overrides WHERE website_id = :wid ORDER BY url_pattern"),
            {"wid": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def add_override(self, website_id: int, url_pattern: str, priority: float | None, changefreq: str | None, include: bool) -> dict:
        row = self.db.execute(
            text(
                "INSERT OR REPLACE INTO sitemap_url_overrides (website_id, url_pattern, priority, changefreq, include) "
                "VALUES (:wid, :pat, :pri, :cf, :inc) RETURNING *"
            ),
            {"wid": website_id, "pat": url_pattern, "pri": priority, "cf": changefreq, "inc": 1 if include else 0},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_override(self, override_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM sitemap_url_overrides WHERE id = :id"), {"id": override_id}
        )
        self.db.commit()
        return result.rowcount > 0

    # --- Pages for sitemap ----------------------------------------------------

    def get_sitemap_pages(self, website_id: int, max_urls: int) -> list[dict]:
        """Get pages suitable for sitemap (excluding non-200 pages)."""
        rows = self.db.execute(
            text(
                "SELECT url, title, modified_at, last_crawled_at "
                "FROM pages WHERE website_id = :wid "
                "AND (status_code IS NULL OR status_code = 200) "
                "ORDER BY url LIMIT :lim"
            ),
            {"wid": website_id, "lim": max_urls},
        ).mappings().all()
        return [dict(r) for r in rows]
