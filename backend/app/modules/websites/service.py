"""Website business logic: CRUD, detection, connectivity test, crawl jobs."""
import asyncio
import logging
import threading

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.integrations.crawler.crawler import crawl_site
from app.modules.pages.service import PagesService
from app.modules.websites import detectors
from app.modules.websites.repository import WebsiteRepository

log = logging.getLogger(__name__)


class WebsiteService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WebsiteRepository(db)

    # --- CRUD ---------------------------------------------------------------

    def list(self, offset: int, limit: int):
        return self.repo.list(offset, limit)

    def get(self, website_id: int) -> dict:
        website = self.repo.get(website_id)
        if not website:
            raise NotFoundError("website.not_found", f"Website {website_id} does not exist")
        return website

    def create(self, name: str, url: str, sitemap_url: str | None) -> dict:
        url = _normalize_url(url)
        if self.repo.get_by_url(url):
            raise ConflictError("website.duplicate", f"Website already exists: {url}")
        return self.repo.create(name, url, sitemap_url)

    def update(self, website_id: int, fields: dict) -> dict:
        self.get(website_id)
        if "url" in fields and fields["url"]:
            fields["url"] = _normalize_url(fields["url"])
        clean = {k: v for k, v in fields.items() if v is not None}
        return self.repo.update(website_id, clean)

    def delete(self, website_id: int) -> None:
        self.get(website_id)
        self.repo.delete(website_id)

    # --- Detection & test ----------------------------------------------------

    async def detect(self, website_id: int) -> dict:
        website = self.get(website_id)
        response = await detectors.fetch(website["url"])
        reachable = response is not None and response.status_code < 400
        platform = "unknown"
        if response is not None:
            platform = detectors.detect_platform_from_html(response.text, dict(response.headers))
        sitemap_url = website["sitemap_url"] or (await detectors.detect_sitemap(website["url"]) if reachable else None)

        updates = {}
        if platform != "unknown" or website["platform"] == "unknown":
            updates["platform"] = platform
        if sitemap_url and sitemap_url != website["sitemap_url"]:
            updates["sitemap_url"] = sitemap_url
        if updates:
            self.repo.update(website_id, updates)

        return {
            "platform": platform,
            "sitemap_url": sitemap_url,
            "reachable": reachable,
            "status_code": response.status_code if response else None,
        }

    async def test(self, website_id: int) -> dict:
        website = self.get(website_id)
        reachable, status_code = await detectors.test_website(website["url"])
        return {"reachable": reachable, "status_code": status_code}

    # --- Crawl jobs -----------------------------------------------------------

    def start_crawl(self, website_id: int, max_pages: int = 500) -> int:
        website = self.get(website_id)
        job_id = self._log_start(website_id, "crawl")
        thread = threading.Thread(
            target=_run_crawl_job,
            args=(website_id, website["url"], website["sitemap_url"], max_pages, job_id),
            daemon=True,
        )
        thread.start()
        return job_id

    def crawl_status(self, job_id: int) -> dict:
        row = self.db.execute(text("SELECT * FROM sync_logs WHERE id = :id"), {"id": job_id}).mappings().first()
        if not row:
            raise NotFoundError("job.not_found", f"Job {job_id} does not exist")
        return dict(row)

    def _log_start(self, website_id: int, sync_type: str) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO sync_logs (module, entity_id, sync_type, status) "
                "VALUES ('crawler', :entity_id, :sync_type, 'running')"
            ),
            {"entity_id": website_id, "sync_type": sync_type},
        )
        self.db.commit()
        return result.lastrowid


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


async def _crawl_with_detection(base_url: str, sitemap_url: str | None, max_pages: int):
    """Discover the sitemap (and platform) on the fly when not stored yet.

    Astro sites commonly ship /sitemap-index.xml, which older detect runs
    missed; discovering here means Crawl works even without an explicit
    Detect step.
    """
    discovered = None
    if not sitemap_url:
        discovered = await detectors.detect_sitemap(base_url)
        sitemap_url = discovered
    pages = await crawl_site(base_url, sitemap_url=sitemap_url, max_pages=max_pages)
    platform = None
    response = await detectors.fetch(base_url)
    if response is not None and response.status_code < 400:
        platform = detectors.detect_platform_from_html(response.text, dict(response.headers))
    return pages, discovered, platform


def _run_crawl_job(website_id: int, base_url: str, sitemap_url: str | None, max_pages: int, job_id: int) -> None:
    """Background worker — owns its own DB session (Rule: one session per unit of work)."""
    from app.database.connection import _SessionFactory

    try:
        parsed, discovered, platform = asyncio.run(
            _crawl_with_detection(base_url, sitemap_url, max_pages)
        )
        session = _SessionFactory()
        try:
            saved = PagesService(session).save_crawl(website_id, parsed)
            # Persist what the job learned so future crawls skip discovery.
            updates = []
            params: dict = {"id": website_id}
            if discovered:
                updates.append("sitemap_url=:sitemap_url")
                params["sitemap_url"] = discovered
            if platform and platform != "unknown":
                updates.append("platform=:platform")
                params["platform"] = platform
            if updates:
                session.execute(
                    text(f"UPDATE websites SET {', '.join(updates)} WHERE id=:id"),
                    params,
                )
            session.execute(
                text(
                    "UPDATE sync_logs SET status='completed', finished_at=datetime('now'), "
                    "records_imported=:records WHERE id=:id"
                ),
                {"records": saved, "id": job_id},
            )
            session.commit()
        finally:
            session.close()
        log.info("crawl job %s completed: %d pages", job_id, saved)
    except Exception as exc:  # noqa: BLE001 — job boundary
        log.exception("crawl job %s failed", job_id)
        try:
            session = _SessionFactory()
            session.execute(
                text(
                    "UPDATE sync_logs SET status='failed', finished_at=datetime('now'), "
                    "error_message=:err WHERE id=:id"
                ),
                {"err": str(exc)[:500], "id": job_id},
            )
            session.commit()
            session.close()
        except Exception:
            log.exception("failed to record job failure")
