"""Page inventory service — persists crawl results."""
from sqlalchemy.orm import Session

from app.integrations.crawler.parser import ParsedPage
from app.modules.pages.repository import PagesRepository


class PagesService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PagesRepository(db)

    def save_crawl(self, website_id: int, pages: list[ParsedPage]) -> int:
        saved = 0
        for page in pages:
            page_id = self.repo.upsert(website_id, page)
            self.repo.replace_links(page_id, page.links, website_id)
            saved += 1
        self.repo.resolve_internal_links(website_id)
        self.db.commit()
        return saved
