"""Report Generator repository — storage and retrieval."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.report_generator.schemas import ReportCreate


class ReportGeneratorRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Reports CRUD
    # ------------------------------------------------------------------

    def create_report(self, data: ReportCreate) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO seo_reports (website_id, title, report_type, format, period_days, status) "
                "VALUES (:wid, :title, :rtype, :fmt, :days, 'pending') "
                "RETURNING *"
            ),
            {
                "wid": data.website_id,
                "title": data.title,
                "rtype": data.report_type.value,
                "fmt": data.format.value,
                "days": data.period_days,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_report(self, report_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM seo_reports WHERE id = :id"),
            {"id": report_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_reports_by_website(self, website_id: int, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT id, title, report_type, format, status, period_days, generated_at, created_at "
                "FROM seo_reports WHERE website_id = :wid ORDER BY created_at DESC LIMIT :lim"
            ),
            {"wid": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_report_status(self, report_id: int, status: str, **kwargs) -> dict:
        updates = ["status = :status"]
        params = {"id": report_id, "status": status}

        if "report_data" in kwargs:
            updates.append("report_data = :data")
            params["data"] = kwargs["report_data"]
        if "file_path" in kwargs:
            updates.append("file_path = :fp")
            params["fp"] = kwargs["file_path"]
        if status == "completed":
            updates.append("generated_at = datetime('now')")

        updates.append("updated_at = datetime('now')")

        row = self.db.execute(
            text(f"UPDATE seo_reports SET {', '.join(updates)} WHERE id = :id RETURNING *"),
            params,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_report(self, report_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM seo_reports WHERE id = :id"),
            {"id": report_id},
        )
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Report Sections
    # ------------------------------------------------------------------

    def add_section(self, report_id: int, section_type: str, title: str, content: str, sort_order: int = 0) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO report_sections (report_id, section_type, title, content, sort_order) "
                "VALUES (:rid, :stype, :title, :content, :order) "
                "RETURNING *"
            ),
            {
                "rid": report_id,
                "stype": section_type,
                "title": title,
                "content": content,
                "order": sort_order,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_sections(self, report_id: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM report_sections WHERE report_id = :rid ORDER BY sort_order"
            ),
            {"rid": report_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def delete_sections(self, report_id: int) -> None:
        self.db.execute(
            text("DELETE FROM report_sections WHERE report_id = :rid"),
            {"rid": report_id},
        )
        self.db.commit()

    # ------------------------------------------------------------------
    # Data Collection
    # ------------------------------------------------------------------

    def get_website(self, website_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT id, name, url FROM websites WHERE id = :id"),
            {"id": website_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_traffic_summary(self, website_id: int, days: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT COALESCE(SUM(clicks), 0) AS total_clicks, "
                "COALESCE(SUM(impressions), 0) AS total_impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions), 4) ELSE 0 END AS avg_ctr, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS avg_position "
                "FROM search_console_data WHERE website_id = :w AND date >= date('now', :days)"
            ),
            {"w": website_id, "days": f"-{days} days"},
        ).mappings().one()
        return dict(row)

    def get_traffic_trend(self, website_id: int, days: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT date, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions), 4) ELSE 0 END AS ctr "
                "FROM search_console_data WHERE website_id = :w AND date >= date('now', :days) "
                "GROUP BY date ORDER BY date"
            ),
            {"w": website_id, "days": f"-{days} days"},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_ranking_distribution(self, website_id: int, days: int) -> dict:
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
            {"w": website_id, "days": f"-{days} days"},
        ).mappings().one()
        return dict(row)

    def get_top_pages(self, website_id: int, days: int, limit: int = 10) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT page_url, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions) * 100, 2) ELSE 0 END AS ctr, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS position "
                "FROM search_console_data WHERE website_id = :w AND page_url IS NOT NULL "
                "AND date >= date('now', :days) GROUP BY page_url ORDER BY clicks DESC LIMIT :lim"
            ),
            {"w": website_id, "days": f"-{days} days", "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_top_queries(self, website_id: int, days: int, limit: int = 10) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT query, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS REAL) / SUM(impressions) * 100, 2) ELSE 0 END AS ctr, "
                "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS position "
                "FROM search_console_data WHERE website_id = :w AND query IS NOT NULL "
                "AND date >= date('now', :days) GROUP BY LOWER(TRIM(query)) ORDER BY impressions DESC LIMIT :lim"
            ),
            {"w": website_id, "days": f"-{days} days", "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_findings(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT severity, rec_type, COUNT(*) AS count "
                "FROM seo_findings WHERE website_id = :w AND status = 'open' "
                "GROUP BY severity, rec_type ORDER BY count DESC"
            ),
            {"w": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_pages_count(self, website_id: int) -> int:
        return self.db.execute(
            text("SELECT COUNT(*) FROM pages WHERE website_id = :w"),
            {"w": website_id},
        ).scalar()

    def get_keywords_count(self, website_id: int, days: int) -> int:
        return self.db.execute(
            text(
                "SELECT COUNT(DISTINCT LOWER(TRIM(query))) FROM search_console_data "
                "WHERE website_id = :w AND query IS NOT NULL AND date >= date('now', :days)"
            ),
            {"w": website_id, "days": f"-{days} days"},
        ).scalar()
