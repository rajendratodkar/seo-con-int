"""Database queries for competitor analysis."""
import re
from sqlalchemy import text
from sqlalchemy.orm import Session


def _normalize(keyword: str) -> str:
    return re.sub(r"\s+", " ", keyword.strip().lower())


class CompetitorRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Competitors ----------------------------------------------------------

    def create_competitor(self, website_id: int, name: str, url: str, notes: str | None) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO competitors (website_id, name, url, notes) "
                "VALUES (:wid, :name, :url, :notes) RETURNING *"
            ),
            {"wid": website_id, "name": name, "url": url, "notes": notes},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_competitor(self, competitor_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM competitors WHERE id = :id"), {"id": competitor_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_competitors(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM competitors WHERE website_id = :wid ORDER BY name"),
            {"wid": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_competitor(self, competitor_id: int, **fields) -> dict | None:
        sets, params = [], {"id": competitor_id}
        for k, v in fields.items():
            if v is not None:
                sets.append(f"{k} = :{k}")
                params[k] = v
        if not sets:
            return self.get_competitor(competitor_id)
        sets.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE competitors SET {', '.join(sets)} WHERE id = :id RETURNING *"), params
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_competitor(self, competitor_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM competitors WHERE id = :id"), {"id": competitor_id})
        self.db.commit()
        return result.rowcount > 0

    # --- Rankings -------------------------------------------------------------

    def upsert_ranking(
        self, competitor_id: int, keyword: str, position: float,
        url: str | None, impressions: int | None, source: str, snapshot_date: str,
    ) -> None:
        normalized = _normalize(keyword)
        self.db.execute(
            text(
                "INSERT INTO competitor_rankings "
                "(competitor_id, keyword, normalized, position, url, impressions, source, snapshot_date) "
                "VALUES (:cid, :kw, :norm, :pos, :url, :imp, :src, :date) "
                "ON CONFLICT (competitor_id, normalized, snapshot_date) DO UPDATE SET "
                "position = excluded.position, url = excluded.url, "
                "impressions = excluded.impressions, source = excluded.source"
            ),
            {"cid": competitor_id, "kw": keyword, "norm": normalized, "pos": position,
             "url": url, "imp": impressions, "src": source, "date": snapshot_date},
        )
        self.db.commit()

    def bulk_upsert_rankings(self, competitor_id: int, rankings: list[dict], snapshot_date: str) -> int:
        count = 0
        for r in rankings:
            self.upsert_ranking(
                competitor_id, r["keyword"], r["position"],
                r.get("url"), r.get("impressions"), r.get("source", "manual"), snapshot_date,
            )
            count += 1
        return count

    def list_rankings(self, competitor_id: int, limit: int = 200) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM competitor_rankings WHERE competitor_id = :cid "
                "ORDER BY position ASC LIMIT :lim"
            ),
            {"cid": competitor_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_competitor_keywords(self, competitor_id: int) -> set[str]:
        """Get all normalized keywords a competitor ranks for."""
        rows = self.db.execute(
            text("SELECT normalized FROM competitor_rankings WHERE competitor_id = :cid"),
            {"cid": competitor_id},
        ).mappings().all()
        return {r.normalized for r in rows}

    def get_competitor_ranking(self, competitor_id: int, normalized: str) -> dict | None:
        row = self.db.execute(
            text(
                "SELECT * FROM competitor_rankings "
                "WHERE competitor_id = :cid AND normalized = :norm "
                "ORDER BY snapshot_date DESC LIMIT 1"
            ),
            {"cid": competitor_id, "norm": normalized},
        ).mappings().one_or_none()
        return dict(row) if row else None

    # --- Content Gaps ---------------------------------------------------------

    def upsert_gap(
        self, website_id: int, keyword: str, competitor_id: int,
        competitor_pos: float, competitor_url: str | None,
        our_position: float | None, opportunity: str,
        search_volume: int | None, priority: float,
    ) -> None:
        self.db.execute(
            text(
                "INSERT INTO content_gaps "
                "(website_id, keyword, competitor_id, competitor_pos, competitor_url, "
                "our_position, opportunity, search_volume, priority) "
                "VALUES (:wid, :kw, :cid, :cpos, :curl, :opos, :opp, :sv, :pri) "
                "ON CONFLICT (website_id, keyword, competitor_id) DO UPDATE SET "
                "competitor_pos = excluded.competitor_pos, competitor_url = excluded.competitor_url, "
                "our_position = excluded.our_position, opportunity = excluded.opportunity, "
                "search_volume = excluded.search_volume, priority = excluded.priority, "
                "updated_at = datetime('now')"
            ),
            {"wid": website_id, "kw": keyword, "cid": competitor_id,
             "cpos": competitor_pos, "curl": competitor_url, "opos": our_position,
             "opp": opportunity, "sv": search_volume, "pri": priority},
        )
        self.db.commit()

    def list_gaps(self, website_id: int, status: str | None = None, limit: int = 100) -> list[dict]:
        conditions = ["website_id = :wid"]
        params: dict = {"wid": website_id, "lim": limit}
        if status:
            conditions.append("status = :status")
            params["status"] = status
        where = " AND ".join(conditions)
        rows = self.db.execute(
            text(
                f"SELECT * FROM content_gaps WHERE {where} "
                f"ORDER BY priority DESC LIMIT :lim"
            ), params,
        ).mappings().all()
        return [dict(r) for r in rows]

    def gap_stats(self, website_id: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN opportunity = 'new_content' THEN 1 ELSE 0 END) AS new_content, "
                "SUM(CASE WHEN opportunity = 'improve_existing' THEN 1 ELSE 0 END) AS improve_existing, "
                "SUM(CASE WHEN opportunity = 'quick_win' THEN 1 ELSE 0 END) AS quick_win "
                "FROM content_gaps WHERE website_id = :wid"
            ),
            {"wid": website_id},
        ).mappings().one()
        return dict(row) if row else {"total": 0, "new_content": 0, "improve_existing": 0, "quick_win": 0}

    def update_gap_status(self, gap_id: int, status: str) -> dict | None:
        row = self.db.execute(
            text("UPDATE content_gaps SET status = :s, updated_at = datetime('now') WHERE id = :id RETURNING *"),
            {"id": gap_id, "s": status},
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_gap(self, gap_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM content_gaps WHERE id = :id"), {"id": gap_id})
        self.db.commit()
        return result.rowcount > 0
