"""SEO analysis orchestration: run engines over crawled data, persist findings."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.engines.search_console.opportunity_engine import find_page_opportunities
from app.engines.seo.analyzer import analyze_page
from app.modules.pages.repository import PagesRepository
from app.modules.seo_analysis.repository import FindingsRepository


class SeoAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.pages = PagesRepository(db)
        self.findings = FindingsRepository(db)

    def run(self, website_id: int) -> dict:
        """Analyze every crawled page of a website and store findings."""
        rules = self.findings.rule_lookup()
        items, total = self.pages.list(website_id, 0, 10000)
        all_urls = {page["url"] for page in items}

        results = []
        saved_findings = 0
        for page in items:
            content = self.pages.get_content(page["id"])
            links = self.pages.get_links(page["id"])
            result = analyze_page(page, content, links, all_urls)
            saved_findings += self.findings.replace_page_findings(
                website_id, page["id"], result["findings"], rules
            )
            results.append({"page_id": page["id"], "url": page["url"], "score": result["score"]})
        self.db.commit()
        return {"pages_analyzed": len(results), "findings_saved": saved_findings, "pages": results}

    def detect_opportunities(self, website_id: int) -> dict:
        """Data-based recommendations from Search Console (Phase 5 milestone)."""
        opportunities = find_page_opportunities(self.db, website_id)
        url_to_page = {
            row.url: row.id
            for row in self.db.execute(
                text("SELECT id, url FROM pages WHERE website_id = :website_id"), {"website_id": website_id}
            )
        }
        for opportunity in opportunities:
            page_id = url_to_page.get(opportunity["page_url"])
            self.findings.save_opportunity(website_id, page_id, opportunity)
        self.db.commit()
        return {"opportunities": len(opportunities)}
