"""Database queries for backlink monitor."""
from urllib.parse import urlparse
from sqlalchemy import text
from sqlalchemy.orm import Session


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


class BacklinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_tables(self) -> None:
        """Create backlinks and backlink_changes tables if they don't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS backlinks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE, "
            "source_url TEXT NOT NULL, "
            "source_domain TEXT NOT NULL, "
            "target_url TEXT NOT NULL, "
            "anchor_text TEXT, "
            "is_nofollow INTEGER NOT NULL DEFAULT 0, "
            "is_sponsored INTEGER NOT NULL DEFAULT 0, "
            "domain_authority INTEGER, "
            "page_authority INTEGER, "
            "status TEXT NOT NULL DEFAULT 'active', "
            "first_seen TEXT NOT NULL DEFAULT (datetime('now')), "
            "last_checked TEXT, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "UNIQUE (website_id, source_url, target_url))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_backlinks_website ON backlinks(website_id)"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_backlinks_domain ON backlinks(source_domain)"
        ))
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS backlink_changes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE, "
            "backlink_id INTEGER REFERENCES backlinks(id) ON DELETE SET NULL, "
            "change_type TEXT NOT NULL, "
            "source_url TEXT NOT NULL, "
            "target_url TEXT NOT NULL, "
            "details TEXT, "
            "detected_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_backlink_changes_website ON backlink_changes(website_id)"
        ))
        self.db.commit()

    # --- Backlinks ------------------------------------------------------------

    def create_backlink(self, data: dict) -> dict:
        data["source_domain"] = _extract_domain(data["source_url"])
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        row = self.db.execute(
            text(f"INSERT OR IGNORE INTO backlinks ({cols}) VALUES ({placeholders}) RETURNING *"),
            data,
        ).mappings().one_or_none()
        self.db.commit()
        if row:
            return dict(row)
        # Already exists — return existing
        existing = self.db.execute(
            text("SELECT * FROM backlinks WHERE website_id = :wid AND source_url = :su AND target_url = :tu"),
            {"wid": data["website_id"], "su": data["source_url"], "tu": data["target_url"]},
        ).mappings().one_or_none()
        return dict(existing) if existing else {}

    def bulk_create(self, backlinks: list[dict]) -> int:
        count = 0
        for bl in backlinks:
            try:
                self.create_backlink(bl)
                count += 1
            except Exception:
                pass
        return count

    def get_backlink(self, backlink_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM backlinks WHERE id = :id"), {"id": backlink_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_backlinks(
        self, website_id: int, status: str | None = None, domain: str | None = None, limit: int = 100,
    ) -> list[dict]:
        conditions = ["website_id = :wid"]
        params: dict = {"wid": website_id, "lim": limit}
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if domain:
            conditions.append("source_domain = :domain")
            params["domain"] = domain
        where = " AND ".join(conditions)
        rows = self.db.execute(
            text(f"SELECT * FROM backlinks WHERE {where} ORDER BY created_at DESC LIMIT :lim"),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_backlink(self, backlink_id: int, **fields) -> dict | None:
        sets, params = [], {"id": backlink_id}
        for k, v in fields.items():
            if v is not None:
                sets.append(f"{k} = :{k}")
                params[k] = v
        if not sets:
            return self.get_backlink(backlink_id)
        sets.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE backlinks SET {', '.join(sets)} WHERE id = :id RETURNING *"), params
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_backlink(self, backlink_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM backlinks WHERE id = :id"), {"id": backlink_id})
        self.db.commit()
        return result.rowcount > 0

    # --- Changes --------------------------------------------------------------

    def log_change(self, website_id: int, backlink_id: int | None, change_type: str,
                    source_url: str, target_url: str, details: str | None = None) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO backlink_changes (website_id, backlink_id, change_type, source_url, target_url, details) "
                "VALUES (:wid, :bid, :ct, :su, :tu, :det) RETURNING *"
            ),
            {"wid": website_id, "bid": backlink_id, "ct": change_type, "su": source_url, "tu": target_url, "det": details},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def list_changes(self, website_id: int, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM backlink_changes WHERE website_id = :wid "
                "ORDER BY detected_at DESC LIMIT :lim"
            ),
            {"wid": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    # --- Profile --------------------------------------------------------------

    def get_profile(self, website_id: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT "
                "COUNT(*) AS total_links, "
                "SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_links, "
                "SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) AS lost_links, "
                "SUM(CASE WHEN status = 'broken' THEN 1 ELSE 0 END) AS broken_links, "
                "COUNT(DISTINCT source_domain) AS unique_domains, "
                "SUM(is_nofollow) AS nofollow_count, "
                "SUM(is_sponsored) AS sponsored_count, "
                "ROUND(AVG(domain_authority), 1) AS avg_da "
                "FROM backlinks WHERE website_id = :wid"
            ),
            {"wid": website_id},
        ).mappings().one()

        top_domains = self.db.execute(
            text(
                "SELECT source_domain, COUNT(*) AS links, MAX(domain_authority) AS max_da "
                "FROM backlinks WHERE website_id = :wid AND status = 'active' "
                "GROUP BY source_domain ORDER BY links DESC LIMIT 10"
            ),
            {"wid": website_id},
        ).mappings().all()

        return {
            **dict(row),
            "top_domains": [dict(d) for d in top_domains],
        }
