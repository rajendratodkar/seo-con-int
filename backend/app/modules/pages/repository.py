"""Data access for crawled pages, content, and links."""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.integrations.crawler.parser import ParsedPage


class PagesRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, website_id: int | None, offset: int, limit: int) -> tuple[list[dict], int]:
        where = "WHERE website_id = :website_id" if website_id else ""
        params: dict = {"limit": limit, "offset": offset}
        if website_id:
            params["website_id"] = website_id
        rows = self.db.execute(
            text(f"SELECT * FROM pages {where} ORDER BY id DESC LIMIT :limit OFFSET :offset"), params
        ).mappings().all()
        total = self.db.execute(text(f"SELECT COUNT(*) FROM pages {where}"), params).scalar_one()
        return [dict(r) for r in rows], total

    def get(self, page_id: int) -> dict | None:
        row = self.db.execute(text("SELECT * FROM pages WHERE id = :id"), {"id": page_id}).mappings().first()
        return dict(row) if row else None

    def get_by_url(self, website_id: int, url: str) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM pages WHERE website_id = :website_id AND url = :url"),
            {"website_id": website_id, "url": url},
        ).mappings().first()
        return dict(row) if row else None

    def upsert(self, website_id: int, page: ParsedPage) -> int:
        existing = self.get_by_url(website_id, page.url)
        if existing:
            self.db.execute(
                text(
                    "UPDATE pages SET canonical_url=:canonical, title=:title, meta_description=:meta, "
                    "status_code=:status_code, published_at=:published, modified_at=:modified, "
                    "crawl_status='done', last_crawled_at=datetime('now'), updated_at=datetime('now') "
                    "WHERE id=:id"
                ),
                {
                    "canonical": page.canonical, "title": page.title, "meta": page.meta_description,
                    "status_code": page.status_code, "published": page.published_at,
                    "modified": page.modified_at, "id": existing["id"],
                },
            )
            page_id = existing["id"]
        else:
            result = self.db.execute(
                text(
                    "INSERT INTO pages (website_id, url, canonical_url, title, meta_description, status_code, "
                    "published_at, modified_at, crawl_status, last_crawled_at) "
                    "VALUES (:website_id, :url, :canonical, :title, :meta, :status_code, :published, :modified, "
                    "'done', datetime('now'))"
                ),
                {
                    "website_id": website_id, "url": page.url, "canonical": page.canonical,
                    "title": page.title, "meta": page.meta_description, "status_code": page.status_code,
                    "published": page.published_at, "modified": page.modified_at,
                },
            )
            page_id = result.lastrowid
        self._save_content(page_id, page)
        return page_id

    def _save_content(self, page_id: int, page: ParsedPage) -> None:
        params = {
            "page_id": page_id,
            "text": page.text_content,
            "headings": json.dumps(page.headings, ensure_ascii=False),
            "images": json.dumps(page.images, ensure_ascii=False),
            "word_count": page.word_count,
            "schema": json.dumps(page.schema_json, ensure_ascii=False),
        }
        exists = self.db.execute(text("SELECT id FROM page_content WHERE page_id = :page_id"), params).first()
        if exists:
            self.db.execute(
                text(
                    "UPDATE page_content SET text_content=:text, headings=:headings, images=:images, "
                    "word_count=:word_count, schema_json=:schema, updated_at=datetime('now') WHERE page_id=:page_id"
                ),
                params,
            )
        else:
            self.db.execute(
                text(
                    "INSERT INTO page_content (page_id, text_content, headings, images, word_count, schema_json) "
                    "VALUES (:page_id, :text, :headings, :images, :word_count, :schema)"
                ),
                params,
            )

    def replace_links(self, page_id: int, links: list[dict], website_id: int) -> None:
        self.db.execute(text("DELETE FROM page_links WHERE page_id = :page_id"), {"page_id": page_id})
        for link in links:
            target = self.get_by_url(website_id, link["target_url"])
            is_internal = 1 if target else 0
            self.db.execute(
                text(
                    "INSERT INTO page_links (page_id, target_url, target_page_id, anchor_text, is_internal, is_nofollow) "
                    "VALUES (:page_id, :target_url, :target_page_id, :anchor, :is_internal, :is_nofollow)"
                ),
                {
                    "page_id": page_id, "target_url": link["target_url"],
                    "target_page_id": target["id"] if target else None,
                    "anchor": link["anchor_text"], "is_internal": is_internal,
                    "is_nofollow": 1 if link["is_nofollow"] else 0,
                },
            )

    def resolve_internal_links(self, website_id: int) -> None:
        """Second pass: link targets discovered after their source pages were saved."""
        self.db.execute(
            text(
                "UPDATE page_links SET target_page_id = ("
                "  SELECT p.id FROM pages p WHERE p.website_id = :website_id AND p.url = page_links.target_url"
                "), is_internal = 1 WHERE target_page_id IS NULL AND EXISTS ("
                "  SELECT 1 FROM pages p WHERE p.website_id = :website_id AND p.url = page_links.target_url)"
            ),
            {"website_id": website_id},
        )

    def get_content(self, page_id: int) -> dict | None:
        row = self.db.execute(text("SELECT * FROM page_content WHERE page_id = :id"), {"id": page_id}).mappings().first()
        return dict(row) if row else None

    def get_links(self, page_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM page_links WHERE page_id = :id ORDER BY id"), {"id": page_id}
        ).mappings().all()
        return [dict(r) for r in rows]
