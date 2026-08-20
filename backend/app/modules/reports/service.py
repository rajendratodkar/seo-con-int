"""Reports: data-based weekly summary (plan §20).

Everything in the report is aggregated from stored facts — no AI narration.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError


class ReportsService:
    def __init__(self, db: Session):
        self.db = db

    def weekly(self, website_id: int) -> dict:
        website = self.db.execute(
            text("SELECT id, name, url FROM websites WHERE id = :id"), {"id": website_id}
        ).mappings().first()
        if website is None:
            raise NotFoundError("website.not_found", f"Website {website_id} does not exist")

        traffic = self._traffic(website_id)
        return {
            "website": dict(website),
            "window_days": 7,
            "traffic": traffic,
            "findings": self._findings_summary(website_id),
            "audit": self._audit_summary(website_id),
            "opportunities": self._opportunities_count(website_id),
            "content": self._content_summary(),
        }

    def _traffic(self, website_id: int) -> dict:
        current = self.db.execute(
            text(
                "SELECT COALESCE(SUM(clicks), 0) AS clicks, COALESCE(SUM(impressions), 0) AS impressions "
                "FROM search_console_data WHERE website_id = :w AND date >= date('now', '-7 days')"
            ),
            {"w": website_id},
        ).mappings().first()
        previous = self.db.execute(
            text(
                "SELECT COALESCE(SUM(clicks), 0) AS clicks, COALESCE(SUM(impressions), 0) AS impressions "
                "FROM search_console_data WHERE website_id = :w "
                "AND date >= date('now', '-14 days') AND date < date('now', '-7 days')"
            ),
            {"w": website_id},
        ).mappings().first()
        return {
            "clicks": current["clicks"],
            "impressions": current["impressions"],
            "clicks_previous": previous["clicks"],
            "impressions_previous": previous["impressions"],
            "clicks_delta": current["clicks"] - previous["clicks"],
            "impressions_delta": current["impressions"] - previous["impressions"],
        }

    def _findings_summary(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT severity, rec_type, COUNT(*) AS n FROM seo_findings "
                "WHERE website_id = :w AND status = 'open' GROUP BY severity, rec_type"
            ),
            {"w": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def _audit_summary(self, website_id: int) -> dict:
        # Computed live (verdicts are never stored — Rule 4)
        from app.modules.content_audit.service import ContentAuditService
        items = ContentAuditService(self.db).audit(website_id)
        summary = {v: 0 for v in ("keep", "improve", "refresh", "consolidate", "review")}
        for item in items:
            summary[item["verdict"]] += 1
        return summary

    def _opportunities_count(self, website_id: int) -> int:
        row = self.db.execute(
            text(
                "SELECT COUNT(*) FROM (SELECT page_url FROM search_console_data "
                "WHERE website_id = :w AND page_url IS NOT NULL AND date >= date('now', '-28 days') "
                "GROUP BY page_url HAVING SUM(impressions) >= 500 AND AVG(position) BETWEEN 4 AND 12)"
            ),
            {"w": website_id},
        ).scalar()
        return row

    def _content_summary(self) -> dict:
        plans = self.db.execute(
            text("SELECT status, COUNT(*) AS n FROM article_plans GROUP BY status")
        ).mappings().all()
        drafts = self.db.execute(
            text("SELECT status, COUNT(*) AS n FROM article_drafts GROUP BY status")
        ).mappings().all()
        return {
            "plans": {r["status"]: r["n"] for r in plans},
            "drafts": {r["status"]: r["n"] for r in drafts},
        }

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def analytics_overview(self, website_id: int, days: int) -> dict:
        """Rich overview: KPIs, traffic trend, top pages, top queries, findings."""
        traffic = self._traffic_range(website_id, days)
        top_pages = self.top_pages(website_id, days, 10)
        top_queries = self.top_queries(website_id, days, 10)
        ranking_dist = self.ranking_distribution(website_id, days)
        findings = self._findings_summary(website_id)
        audit = self._audit_summary(website_id)
        pages_count = self.db.execute(
            text("SELECT COUNT(*) FROM pages WHERE website_id = :w"), {"w": website_id}
        ).scalar()
        keywords_count = self.db.execute(
            text("SELECT COUNT(DISTINCT LOWER(TRIM(query))) FROM search_console_data "
                 "WHERE website_id = :w AND query IS NOT NULL AND date >= date('now', :days)"),
            {"w": website_id, "days": f'-{days} days'},
        ).scalar()
        return {
            "period_days": days,
            "kpis": {
                "total_clicks": traffic["total_clicks"],
                "total_impressions": traffic["total_impressions"],
                "avg_ctr": traffic["avg_ctr"],
                "avg_position": traffic["avg_position"],
                "pages_indexed": pages_count,
                "unique_queries": keywords_count,
            },
            "traffic_trend": self.traffic_trend(website_id, days),
            "top_pages": top_pages,
            "top_queries": top_queries,
            "ranking_distribution": ranking_dist,
            "findings": findings,
            "audit": audit,
        }

    def _traffic_range(self, website_id: int, days: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT COALESCE(SUM(clicks), 0) AS total_clicks, "
                "COALESCE(SUM(impressions), 0) AS total_impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions), 4) ELSE 0 END AS avg_ctr, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS avg_position "
                "FROM search_console_data WHERE website_id = :w AND date >= date('now', :days)"
            ),
            {"w": website_id, "days": f'-{days} days'},
        ).mappings().one()
        return dict(row)

    def traffic_trend(self, website_id: int, days: int) -> list[dict]:
        """Daily traffic trend."""
        rows = self.db.execute(
            text(
                "SELECT date, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions), 4) ELSE 0 END AS ctr "
                "FROM search_console_data WHERE website_id = :w AND date >= date('now', :days) "
                "GROUP BY date ORDER BY date"
            ),
            {"w": website_id, "days": f'-{days} days'},
        ).mappings().all()
        return [dict(r) for r in rows]

    def ranking_distribution(self, website_id: int, days: int) -> dict:
        """How keywords distribute across position buckets."""
        row = self.db.execute(
            text(
                "SELECT "
                "SUM(CASE WHEN avg_pos <= 3 THEN 1 ELSE 0 END) AS top_3, "
                "SUM(CASE WHEN avg_pos > 3 AND avg_pos <= 10 THEN 1 ELSE 0 END) AS pos_4_10, "
                "SUM(CASE WHEN avg_pos > 10 AND avg_pos <= 20 THEN 1 ELSE 0 END) AS pos_11_20, "
                "SUM(CASE WHEN avg_pos > 20 THEN 1 ELSE 0 END) AS pos_21_plus "
                "FROM (SELECT query, MIN(position) AS avg_pos FROM search_console_data "
                "WHERE website_id = :w AND query IS NOT NULL AND date >= date('now', :days) "
                "GROUP BY LOWER(TRIM(query)))"
            ),
            {"w": website_id, "days": f'-{days} days'},
        ).mappings().one()
        return dict(row)

    def top_pages(self, website_id: int, days: int, limit: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT page_url, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions) * 100, 2) ELSE 0 END AS ctr, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS position "
                "FROM search_console_data WHERE website_id = :w AND page_url IS NOT NULL "
                "AND date >= date('now', :days) GROUP BY page_url ORDER BY clicks DESC LIMIT :lim"
            ),
            {"w": website_id, "days": f'-{days} days', "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def top_queries(self, website_id: int, days: int, limit: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT query, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions) * 100, 2) ELSE 0 END AS ctr, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS position "
                "FROM search_console_data WHERE website_id = :w AND query IS NOT NULL "
                "AND date >= date('now', :days) GROUP BY LOWER(TRIM(query)) ORDER BY impressions DESC LIMIT :lim"
            ),
            {"w": website_id, "days": f'-{days} days', "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]
