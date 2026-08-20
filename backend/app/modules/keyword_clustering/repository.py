"""Database queries for keyword clustering.

Uses the existing `topic_clusters` and `topic_cluster_pages` tables,
plus a new `keyword_cluster_items` junction table for keyword-to-cluster mapping.
"""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class KeywordClusterRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_table(self) -> None:
        """Create the keyword_cluster_items table if it doesn't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS keyword_cluster_items ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "cluster_id INTEGER NOT NULL REFERENCES topic_clusters(id) ON DELETE CASCADE, "
            "keyword TEXT NOT NULL, "
            "search_volume INTEGER, "
            "position REAL, "
            "source TEXT NOT NULL DEFAULT 'manual', "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "UNIQUE (cluster_id, keyword))"
        ))
        self.db.commit()

    # --- Clusters (backed by topic_clusters) ---------------------------------

    def create_cluster(
        self, website_id: int, name: str, description: str | None, pillar_keyword: str | None,
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO topic_clusters (website_id, name, description) "
                "VALUES (:wid, :name, :desc) RETURNING *"
            ),
            {"wid": website_id, "name": name, "desc": description},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_cluster(self, cluster_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM topic_clusters WHERE id = :id"), {"id": cluster_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_clusters(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM topic_clusters WHERE website_id = :wid ORDER BY name"),
            {"wid": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_cluster(self, cluster_id: int, **fields) -> dict | None:
        sets, params = [], {"id": cluster_id}
        for k, v in fields.items():
            if v is not None:
                sets.append(f"{k} = :{k}")
                params[k] = v
        if not sets:
            return self.get_cluster(cluster_id)
        sets.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE topic_clusters SET {', '.join(sets)} WHERE id = :id RETURNING *"), params
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_cluster(self, cluster_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM topic_clusters WHERE id = :id"), {"id": cluster_id})
        self.db.commit()
        return result.rowcount > 0

    # --- Keywords in clusters -------------------------------------------------

    def add_keyword(
        self, cluster_id: int, keyword: str,
        search_volume: int | None = None, position: float | None = None,
        source: str = "manual",
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO keyword_cluster_items (cluster_id, keyword, search_volume, position, source) "
                "VALUES (:cid, :kw, :sv, :pos, :src) RETURNING *"
            ),
            {"cid": cluster_id, "kw": keyword, "sv": search_volume, "pos": position, "src": source},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def bulk_add_keywords(
        self, cluster_id: int, keywords: list[dict], source: str = "manual",
    ) -> int:
        count = 0
        for kw in keywords:
            try:
                self.add_keyword(
                    cluster_id, kw["keyword"],
                    kw.get("search_volume"), kw.get("position"), source,
                )
                count += 1
            except Exception:
                pass  # Skip duplicates
        return count

    def list_keywords(self, cluster_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM keyword_cluster_items WHERE cluster_id = :cid ORDER BY keyword"),
            {"cid": cluster_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def remove_keyword(self, item_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM keyword_cluster_items WHERE id = :id"), {"id": item_id}
        )
        self.db.commit()
        return result.rowcount > 0

    def get_keyword_count(self, cluster_id: int) -> int:
        return self.db.execute(
            text("SELECT COUNT(*) FROM keyword_cluster_items WHERE cluster_id = :cid"),
            {"cid": cluster_id},
        ).scalar()

    # --- Import from existing keywords table ---------------------------------

    def import_from_keywords(self, website_id: int, cluster_id: int) -> int:
        """Import keywords from the main keywords table into a cluster."""
        rows = self.db.execute(
            text(
                "SELECT keyword, source FROM keywords WHERE website_id = :wid "
                "AND normalized NOT IN ("
                "  SELECT LOWER(keyword) FROM keyword_cluster_items WHERE cluster_id = :cid"
                ")"
            ),
            {"wid": website_id, "cid": cluster_id},
        ).mappings().all()
        count = 0
        for r in rows:
            try:
                self.add_keyword(cluster_id, r["keyword"], source=r.get("source", "manual"))
                count += 1
            except Exception:
                pass
        return count

    # --- Get all keywords for clustering -------------------------------------

    def get_website_keywords(self, website_id: int) -> list[str]:
        """Get all unique keywords from SC data for a website."""
        rows = self.db.execute(
            text(
                "SELECT DISTINCT LOWER(TRIM(query)) AS kw FROM search_console_data "
                "WHERE website_id = :wid AND query IS NOT NULL "
                "AND impressions >= 10 ORDER BY kw"
            ),
            {"wid": website_id},
        ).mappings().all()
        return [r.kw for r in rows]
