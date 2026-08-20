"""Bulk operation business logic: manage background jobs for bulk actions."""
import asyncio
import logging
import threading

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.connection import _SessionFactory

log = logging.getLogger(__name__)


class BulkOperationService:
    """Service for managing bulk operation jobs."""

    def __init__(self, db: Session):
        self.db = db

    def get_job(self, job_id: int) -> dict:
        """Get bulk operation job status."""
        row = self.db.execute(
            text("SELECT * FROM sync_logs WHERE id = :id"),
            {"id": job_id}
        ).mappings().first()
        if not row:
            raise NotFoundError("job.not_found", f"Bulk job {job_id} does not exist")
        return dict(row)

    def list_jobs(self, operation: str | None = None, limit: int = 20) -> list[dict]:
        """List bulk operation jobs, optionally filtered by operation type."""
        if operation:
            rows = self.db.execute(
                text(
                    "SELECT * FROM sync_logs "
                    "WHERE module = 'bulk' AND sync_type = :operation "
                    "ORDER BY id DESC LIMIT :limit"
                ),
                {"operation": operation, "limit": limit}
            ).mappings().all()
        else:
            rows = self.db.execute(
                text(
                    "SELECT * FROM sync_logs "
                    "WHERE module = 'bulk' "
                    "ORDER BY id DESC LIMIT :limit"
                ),
                {"limit": limit}
            ).mappings().all()
        return [dict(r) for r in rows]

    def start_bulk_crawl(self, website_ids: list[int], max_pages_per_site: int = 50) -> int:
        """Start bulk crawl for multiple websites."""
        job_id = self._log_start("bulk_crawl", len(website_ids))
        thread = threading.Thread(
            target=_run_bulk_crawl,
            args=(website_ids, max_pages_per_site, job_id),
            daemon=True,
        )
        thread.start()
        return job_id

    def start_bulk_analyze(self, website_ids: list[int], page_limit: int = 100) -> int:
        """Start bulk SEO analysis for multiple websites."""
        job_id = self._log_start("bulk_analyze", len(website_ids))
        thread = threading.Thread(
            target=_run_bulk_analyze,
            args=(website_ids, page_limit, job_id),
            daemon=True,
        )
        thread.start()
        return job_id

    def start_bulk_ideas(self, website_ids: list[int], sources: list[str]) -> int:
        """Start bulk idea generation for multiple websites."""
        job_id = self._log_start("bulk_ideas", len(website_ids))
        thread = threading.Thread(
            target=_run_bulk_ideas,
            args=(website_ids, sources, job_id),
            daemon=True,
        )
        thread.start()
        return job_id

    def _log_start(self, sync_type: str, total_items: int) -> int:
        """Log job start to sync_logs table."""
        result = self.db.execute(
            text(
                "INSERT INTO sync_logs (module, sync_type, status, records_imported) "
                "VALUES ('bulk', :sync_type, 'running', :total)"
            ),
            {"sync_type": sync_type, "total": total_items},
        )
        self.db.commit()
        return result.lastrowid

    def _update_job(self, job_id: int, status: str, completed: int = 0, failed: int = 0, error: str | None = None):
        """Update job status in sync_logs."""
        try:
            session = _SessionFactory()
            session.execute(
                text(
                    "UPDATE sync_logs SET "
                    "status = :status, "
                    "records_imported = :completed, "
                    "error_message = :error, "
                    "finished_at = CASE WHEN :status IN ('completed', 'failed') THEN datetime('now') ELSE finished_at END "
                    "WHERE id = :id"
                ),
                {"status": status, "completed": completed, "error": error, "id": job_id},
            )
            session.commit()
            session.close()
        except Exception:
            log.exception("failed to update bulk job %s", job_id)


def _run_bulk_crawl(website_ids: list[int], max_pages_per_site: int, job_id: int) -> None:
    """Background worker for bulk crawl."""
    from app.modules.websites.service import WebsiteService

    completed = 0
    failed = 0
    service = BulkOperationService(_SessionFactory())

    for website_id in website_ids:
        try:
            session = _SessionFactory()
            try:
                ws = WebsiteService(session)
                ws.start_crawl(website_id, max_pages_per_site)
                completed += 1
            finally:
                session.close()
        except Exception as exc:
            log.exception("bulk crawl failed for website %s", website_id)
            failed += 1
        service._update_job(job_id, "running", completed, failed)

    final_status = "completed" if failed == 0 else "completed"
    service._update_job(job_id, final_status, completed, failed)
    log.info("bulk crawl job %s completed: %d/%d websites", job_id, completed, len(website_ids))


def _run_bulk_analyze(website_ids: list[int], page_limit: int, job_id: int) -> None:
    """Background worker for bulk SEO analysis."""
    from app.modules.seo_analysis.service import SeoAnalysisService

    completed = 0
    failed = 0
    service = BulkOperationService(_SessionFactory())

    for website_id in website_ids:
        try:
            session = _SessionFactory()
            try:
                seo = SeoAnalysisService(session)
                seo.run(website_id)
                completed += 1
            finally:
                session.close()
        except Exception as exc:
            log.exception("bulk analyze failed for website %s", website_id)
            failed += 1
        service._update_job(job_id, "running", completed, failed)

    service._update_job(job_id, "completed", completed, failed)
    log.info("bulk analyze job %s completed: %d/%d websites", job_id, completed, len(website_ids))


def _run_bulk_ideas(website_ids: list[int], sources: list[str], job_id: int) -> None:
    """Background worker for bulk idea generation."""
    from app.modules.content_ideas.service import ContentIdeasService

    completed = 0
    failed = 0
    service = BulkOperationService(_SessionFactory())

    for website_id in website_ids:
        try:
            session = _SessionFactory()
            try:
                cs = ContentIdeasService(session)
                cs.generate(website_id)
                completed += 1
            finally:
                session.close()
        except Exception as exc:
            log.exception("bulk ideas failed for website %s", website_id)
            failed += 1
        service._update_job(job_id, "running", completed, failed)

    service._update_job(job_id, "completed", completed, failed)
    log.info("bulk ideas job %s completed: %d/%d websites", job_id, completed, len(website_ids))
