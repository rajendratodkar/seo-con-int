"""Content audit: per-page verdicts computed from data (Rule 4 — never stored as fact).

Verdicts: keep · improve · refresh · consolidate · review
"""
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

STALE_DAYS = 365

VERDICTS = ("keep", "improve", "refresh", "consolidate", "review")


class ContentAuditService:
    def __init__(self, db: Session):
        self.db = db

    def audit(self, website_id: int) -> list[dict]:
        pages = self.db.execute(
            text("SELECT * FROM pages WHERE website_id = :website_id"), {"website_id": website_id}
        ).mappings().all()

        # Traffic per page (last 28 days)
        traffic = {
            row.page_url: row
            for row in self.db.execute(
                text(
                    "SELECT page_url, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                    "AVG(position) AS avg_position FROM search_console_data "
                    "WHERE website_id = :website_id AND date >= date('now', '-28 days') AND page_url IS NOT NULL "
                    "GROUP BY page_url"
                ),
                {"website_id": website_id},
            )
        }

        # Query overlap for consolidation signals: query -> pages ranking for it
        query_pages: dict[str, set[str]] = {}
        for row in self.db.execute(
            text(
                "SELECT query, page_url FROM search_console_data "
                "WHERE website_id = :website_id AND date >= date('now', '-28 days') "
                "AND query IS NOT NULL AND impressions >= 20 GROUP BY query, page_url"
            ),
            {"website_id": website_id},
        ):
            query_pages.setdefault(row.query, set()).add(row.page_url)
        cannibalized = {
            page for urls in query_pages.values() if len(urls) >= 3 for page in urls
        }

        results = []
        for page in pages:
            t = traffic.get(page["url"])
            verdict, reason = self._verdict(page, t, page["url"] in cannibalized)
            results.append({
                "page_id": page["id"],
                "url": page["url"],
                "title": page["title"],
                "verdict": verdict,
                "reason": reason,
                "clicks": t["clicks"] if t else 0,
                "impressions": t["impressions"] if t else 0,
            })
        results.sort(key=lambda r: -r["impressions"])
        return results

    def _verdict(self, page: dict, traffic, cannibalized: bool) -> tuple[str, str]:
        if page["status_code"] and page["status_code"] >= 400:
            return "review", f"HTTP {page['status_code']} on last crawl"
        if cannibalized:
            return "consolidate", "3+ pages rank for the same queries — consolidation candidate"
        if traffic and traffic["impressions"] >= 500 and 4 <= traffic["avg_position"] <= 12:
            return "improve", f"Position {traffic['avg_position']:.1f} with {traffic['impressions']:,} impressions"
        if self._is_stale(page.get("published_at")):
            return "refresh", "Content older than 12 months"
        if traffic and traffic["clicks"] > 0:
            return "keep", "Receiving clicks with no ranking weakness detected"
        return "review", "Insufficient data — manual review needed"

    @staticmethod
    def _is_stale(published: str | None) -> bool:
        if not published:
            return False
        try:
            parsed = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            return False
        age_days = (datetime.now(timezone.utc) - parsed).days
        return age_days > STALE_DAYS
