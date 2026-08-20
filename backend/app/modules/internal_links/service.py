"""Internal link recommendations (data-based, plan §19).

Two pages are link candidates when they share Search Console queries or live in
the same topic cluster but do not link to each other yet. Every suggestion
carries the reason — never a bare list.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError


class InternalLinksService:
    def __init__(self, db: Session):
        self.db = db

    def suggest(self, website_id: int, limit: int = 30) -> list[dict]:
        suggestions = self._from_shared_queries(website_id, limit)
        suggestions += self._from_clusters(website_id, limit - len(suggestions))

        # Drop pairs already linked (in either direction)
        existing = {
            (row[0], row[1]) for row in self.db.execute(
                text(
                    "SELECT pl.page_id, pl.target_page_id FROM page_links pl "
                    "JOIN pages p ON p.id = pl.page_id WHERE p.website_id = :w AND pl.is_internal = 1"
                ),
                {"w": website_id},
            )
        }
        fresh, seen = [], set()
        for s in suggestions:
            pair = (s["source_page_id"], s["target_page_id"])
            if pair in existing or tuple(reversed(pair)) in seen or pair in seen:
                continue
            seen.add(pair)
            fresh.append(s)
        return fresh[:limit]

    def _from_shared_queries(self, website_id: int, limit: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT a.page_url AS url_a, b.page_url AS url_b, COUNT(DISTINCT a.query) AS shared, "
                "SUM(a.impressions) AS impressions "
                "FROM search_console_data a "
                "JOIN search_console_data b ON b.query = a.query AND b.page_url > a.page_url "
                " AND b.website_id = a.website_id AND b.date = a.date "
                "WHERE a.website_id = :w AND a.query IS NOT NULL AND a.page_url IS NOT NULL "
                " AND a.date >= date('now', '-28 days') "
                "GROUP BY a.page_url, b.page_url HAVING shared >= 2 "
                "ORDER BY impressions DESC LIMIT :limit"
            ),
            {"w": website_id, "limit": max(limit, 0) * 2},
        ).mappings().all()

        suggestions = []
        pages = {row["url"]: row["id"] for row in self.db.execute(
            text("SELECT id, url FROM pages WHERE website_id = :w"), {"w": website_id}
        ).mappings().all()}
        for row in rows:
            source_id, target_id = pages.get(row["url_a"]), pages.get(row["url_b"])
            if not source_id or not target_id:
                continue
            suggestions.append({
                "website_id": website_id,
                "source_page_id": source_id,
                "target_page_id": target_id,
                "recommendation": (
                    f"Link '{row['url_a']}' → '{row['url_b']}'"
                ),
                "why": (
                    f"Both pages rank for {row['shared']} shared queries with "
                    f"{row['impressions']:,} combined impressions (last 28 days)."
                ),
            })
        return suggestions

    def _from_clusters(self, website_id: int, limit: int) -> list[dict]:
        if limit <= 0:
            return []
        rows = self.db.execute(
            text(
                "SELECT tc.id AS cluster_id, tc.name, tc.pillar_page_id, tcp.page_id "
                "FROM topic_clusters tc JOIN topic_cluster_pages tcp ON tcp.cluster_id = tc.id "
                "WHERE tc.website_id = :w AND tc.pillar_page_id IS NOT NULL"
            ),
            {"w": website_id},
        ).mappings().all()
        suggestions = []
        for row in rows:
            if row["page_id"] == row["pillar_page_id"]:
                continue
            suggestions.append({
                "website_id": website_id,
                "source_page_id": row["page_id"],
                "target_page_id": row["pillar_page_id"],
                "recommendation": f"Link support page → pillar in cluster '{row['name']}'",
                "why": f"Both pages belong to the '{row['name']}' topic cluster; support pages should link to the pillar.",
            })
        return suggestions[:limit]

    def save(self, website_id: int, source_page_id: int, target_page_id: int,
             recommendation: str | None, why: str | None) -> dict:
        result = self.db.execute(
            text(
                "INSERT OR IGNORE INTO internal_links (website_id, source_page_id, target_page_id, recommendation) "
                "VALUES (:w, :s, :t, :r)"
            ),
            {"w": website_id, "s": source_page_id, "t": target_page_id,
             "r": f"{recommendation} — {why}" if recommendation else why},
        )
        self.db.commit()
        row = self.db.execute(
            text(
                "SELECT * FROM internal_links WHERE website_id = :w AND source_page_id = :s AND target_page_id = :t"
            ),
            {"w": website_id, "s": source_page_id, "t": target_page_id},
        ).mappings().first()
        return dict(row) if row else {"saved": result.rowcount > 0}

    def list(self, website_id: int, status: str | None) -> list[dict]:
        where = "WHERE website_id = :w" + (" AND status = :s" if status else "")
        params = {"w": website_id} | ({"s": status} if status else {})
        rows = self.db.execute(
            text("SELECT * FROM internal_links " + where + " ORDER BY id DESC"), params
        ).mappings().all()
        return [dict(r) for r in rows]

    def set_status(self, link_id: int, status: str) -> dict:
        from app.core.exceptions import AppError
        if status not in ("suggested", "applied", "dismissed"):
            raise AppError("link.invalid_status", "status must be suggested|applied|dismissed")
        row = self.db.execute(text("SELECT id FROM internal_links WHERE id = :id"), {"id": link_id}).first()
        if row is None:
            raise NotFoundError("link.not_found", f"Internal link {link_id} does not exist")
        self.db.execute(
            text("UPDATE internal_links SET status = :s WHERE id = :id"), {"id": link_id, "s": status}
        )
        self.db.commit()
        return dict(self.db.execute(
            text("SELECT * FROM internal_links WHERE id = :id"), {"id": link_id}
        ).mappings().first())
