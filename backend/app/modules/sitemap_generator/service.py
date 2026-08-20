"""Sitemap Generator service — generates XML sitemaps from crawled pages."""
import fnmatch
import logging
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

from sqlalchemy.orm import Session

from app.modules.sitemap_generator.repository import SitemapRepository

logger = logging.getLogger(__name__)


class SitemapGeneratorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SitemapRepository(db)
        self.repo.ensure_tables()

    def get_settings(self, website_id: int) -> dict:
        return self.repo.get_settings(website_id) or {
            "website_id": website_id,
            "default_priority": 0.5,
            "default_changefreq": "weekly",
            "include_images": True,
            "include_news": False,
            "max_urls": 50000,
            "exclude_patterns": [],
        }

    def update_settings(self, website_id: int, **fields) -> dict:
        return self.repo.upsert_settings(website_id, **fields)

    def list_overrides(self, website_id: int) -> list[dict]:
        return self.repo.list_overrides(website_id)

    def add_override(self, website_id: int, url_pattern: str, priority: float | None, changefreq: str | None, include: bool) -> dict:
        return self.repo.add_override(website_id, url_pattern, priority, changefreq, include)

    def delete_override(self, override_id: int) -> dict:
        if not self.repo.delete_override(override_id):
            from app.core.exceptions import NotFoundError
            raise NotFoundError("sitemap.override_not_found", f"Override {override_id} not found")
        return {"deleted": True, "id": override_id}

    def generate(self, website_id: int) -> dict:
        """Generate XML sitemap for a website."""
        settings = self.get_settings(website_id)
        overrides = self.repo.list_overrides(website_id)
        pages = self.repo.get_sitemap_pages(website_id, settings.get("max_urls", 50000))

        # Build exclusion patterns
        exclude_patterns = settings.get("exclude_patterns") or []

        # Build XML
        urlset = Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        if settings.get("include_images"):
            urlset.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")

        included = 0
        excluded = 0

        for page in pages:
            url = page["url"]

            # Check exclusions
            if self._is_excluded(url, exclude_patterns):
                excluded += 1
                continue

            # Apply overrides
            priority, changefreq, include = self._apply_overrides(url, overrides, settings)
            if not include:
                excluded += 1
                continue

            url_el = SubElement(urlset, "url")
            SubElement(url_el, "loc").text = url

            # Last modified
            lastmod = page.get("modified_at") or page.get("last_crawled_at")
            if lastmod:
                SubElement(url_el, "lastmod").text = lastmod[:10]  # YYYY-MM-DD

            SubElement(url_el, "changefreq").text = changefreq
            SubElement(url_el, "priority").text = str(priority)

            # Images (if enabled)
            if settings.get("include_images"):
                self._add_images(url_el, page.get("title"), url)

            included += 1

        # Pretty print
        rough = tostring(urlset, encoding="unicode")
        xml = parseString(rough).toprettyxml(indent="  ", encoding=None)
        # Remove extra XML declaration line
        lines = xml.split("\n")
        if lines[0].startswith("<?xml"):
            lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
        xml = "\n".join(lines)

        return {
            "xml": xml,
            "url_count": included,
            "excluded_count": excluded,
            "total_pages": len(pages),
        }

    @staticmethod
    def _is_excluded(url: str, patterns: list[str]) -> bool:
        for pattern in patterns:
            if fnmatch.fnmatch(url, pattern):
                return True
        return False

    @staticmethod
    def _apply_overrides(url: str, overrides: list[dict], settings: dict) -> tuple[float, str, bool]:
        priority = settings.get("default_priority", 0.5)
        changefreq = settings.get("default_changefreq", "weekly")
        include = True

        for o in overrides:
            if fnmatch.fnmatch(url, o["url_pattern"]):
                if o.get("priority") is not None:
                    priority = o["priority"]
                if o.get("changefreq"):
                    changefreq = o["changefreq"]
                if not o.get("include", True):
                    include = False

        return priority, changefreq, include

    @staticmethod
    def _add_images(url_el, title: str | None, page_url: str) -> None:
        """Add image:image elements (placeholder — real implementation would parse page content)."""
        if title:
            img_el = SubElement(url_el, "{http://www.google.com/schemas/sitemap-image/1.1}image")
            SubElement(img_el, "{http://www.google.com/schemas/sitemap-image/1.1}title").text = title
