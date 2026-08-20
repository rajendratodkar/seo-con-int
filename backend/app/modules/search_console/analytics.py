"""Search Console analytics: query/page aggregation and period comparison."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class SearchConsoleAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def top_queries(self, website_id: int, start: str, end: str, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT query, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "AVG(position) AS avg_position, CASE WHEN SUM(impressions) > 0 "
                "THEN CAST(SUM(clicks) AS REAL) / SUM(impressions) ELSE 0 END AS ctr "
                "FROM search_console_data "
                "WHERE website_id = :website_id AND date BETWEEN :start AND :end AND query IS NOT NULL "
                "GROUP BY query ORDER BY impressions DESC LIMIT :limit"
            ),
            {"website_id": website_id, "start": start, "end": end, "limit": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def top_pages(self, website_id: int, start: str, end: str, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT page_url, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "AVG(position) AS avg_position, CASE WHEN SUM(impressions) > 0 "
                "THEN CAST(SUM(clicks) AS REAL) / SUM(impressions) ELSE 0 END AS ctr "
                "FROM search_console_data "
                "WHERE website_id = :website_id AND date BETWEEN :start AND :end AND page_url IS NOT NULL "
                "GROUP BY page_url ORDER BY impressions DESC LIMIT :limit"
            ),
            {"website_id": website_id, "start": start, "end": end, "limit": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def compare_periods(
        self, website_id: int, current_start: str, current_end: str, previous_start: str, previous_end: str
    ) -> dict:
        current = self._totals(website_id, current_start, current_end)
        previous = self._totals(website_id, previous_start, previous_end)
        return {
            "current": {**current, "start": current_start, "end": current_end},
            "previous": {**previous, "start": previous_start, "end": previous_end},
            "delta": {
                "clicks": current["clicks"] - previous["clicks"],
                "impressions": current["impressions"] - previous["impressions"],
            },
        }

    def _totals(self, website_id: int, start: str, end: str) -> dict:
        row = self.db.execute(
            text(
                "SELECT COALESCE(SUM(clicks), 0) AS clicks, COALESCE(SUM(impressions), 0) AS impressions "
                "FROM search_console_data WHERE website_id = :website_id AND date BETWEEN :start AND :end"
            ),
            {"website_id": website_id, "start": start, "end": end},
        ).mappings().first()
        return dict(row)
