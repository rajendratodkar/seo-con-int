"""SEO Checklist service — auto-generate from findings and manage status."""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.seo_checklist.repository import ChecklistRepository

logger = logging.getLogger(__name__)

# Category mappings from finding rec_type and rule categories
CATEGORY_MAP = {
    "meta": "meta",
    "content": "content",
    "technical": "technical",
    "links": "links",
    "structured_data": "structured_data",
    "performance": "performance",
}


def _categorize_finding(finding: dict) -> str:
    """Map a finding to a checklist category."""
    rec_type = finding.get("rec_type", "")
    evidence = (finding.get("evidence", "") + finding.get("recommendation", "")).lower()
    if "title" in evidence or "meta" in evidence or "description" in evidence:
        return "meta"
    if "heading" in evidence or "content" in evidence or "keyword" in evidence:
        return "content"
    if "link" in evidence or "anchor" in evidence:
        return "links"
    if "schema" in evidence or "structured" in evidence:
        return "structured_data"
    if "speed" in evidence or "core web" in evidence or "lcp" in evidence:
        return "performance"
    if "canonical" in evidence or "redirect" in evidence or "crawl" in evidence:
        return "technical"
    return "technical"  # default


class ChecklistService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChecklistRepository(db)
        self.repo.ensure_tables()

    def get_or_create(self, website_id: int, page_id: int) -> dict:
        return self.repo.get_or_create_checklist(website_id, page_id)

    def list(self, website_id: int) -> list[dict]:
        return self.repo.list_checklists(website_id)

    def detail(self, checklist_id: int) -> dict:
        c = self.repo.get_checklist(checklist_id)
        if not c:
            raise NotFoundError("checklist.not_found", f"Checklist {checklist_id} not found")
        items = self.repo.get_items(checklist_id)
        stats = self.repo._item_stats(checklist_id)

        # Get page info
        page = self.db.execute(
            text("SELECT url, title FROM pages WHERE id = :pid"), {"pid": c["page_id"]}
        ).mappings().one_or_none()

        return {
            **c,
            **stats,
            "items": items,
            "page_url": page["url"] if page else None,
            "page_title": page["title"] if page else None,
        }

    def auto_generate(self, checklist_id: int) -> dict:
        """Auto-populate checklist from SEO findings for the page."""
        c = self.repo.get_checklist(checklist_id)
        if not c:
            raise NotFoundError("checklist.not_found", f"Checklist {checklist_id} not found")

        # Get existing findings for this page
        findings = self.db.execute(
            text(
                "SELECT id, recommendation, why, evidence, severity, rec_type "
                "FROM seo_findings WHERE page_id = :pid AND status = 'open'"
            ),
            {"pid": c["page_id"]},
        ).mappings().all()

        # Get existing item text to avoid duplicates
        existing_items = {item["item_text"] for item in self.repo.get_items(checklist_id)}

        items = []
        for f in findings:
            category = _categorize_finding(dict(f))
            item_text = f.recommendation
            if item_text not in existing_items:
                items.append({
                    "category": category,
                    "item_text": item_text,
                    "notes": f.why,
                    "finding_id": f.id,
                })
                existing_items.add(item_text)

        # Add standard SEO checklist items if not already present
        standard_items = self._standard_items()
        for item in standard_items:
            if item["item_text"] not in existing_items:
                items.append(item)
                existing_items.add(item["item_text"])

        count = self.repo.bulk_add_items(checklist_id, items)
        return {"items_added": count, "total_findings": len(findings)}

    def add_item(self, checklist_id: int, category: str, item_text: str, notes: str | None = None) -> dict:
        return self.repo.add_item(checklist_id, category, item_text, notes)

    def update_item(self, item_id: int, status: str | None = None, notes: str | None = None) -> dict:
        fields = {}
        if status:
            fields["status"] = status
        if notes is not None:
            fields["notes"] = notes
        result = self.repo.update_item(item_id, **fields)
        if not result:
            raise NotFoundError("checklist.item_not_found", f"Item {item_id} not found")
        return result

    def delete_item(self, item_id: int) -> dict:
        if not self.repo.delete_item(item_id):
            raise NotFoundError("checklist.item_not_found", f"Item {item_id} not found")
        return {"deleted": True, "id": item_id}

    def complete_checklist(self, checklist_id: int) -> dict:
        result = self.repo.update_checklist_status(checklist_id, "completed")
        if not result:
            raise NotFoundError("checklist.not_found", f"Checklist {checklist_id} not found")
        return result

    def delete_checklist(self, checklist_id: int) -> dict:
        if not self.repo.delete_checklist(checklist_id):
            raise NotFoundError("checklist.not_found", f"Checklist {checklist_id} not found")
        return {"deleted": True, "id": checklist_id}

    @staticmethod
    def _standard_items() -> list[dict]:
        """Standard SEO checklist items to always include."""
        return [
            {"category": "meta", "item_text": "Title tag is unique and under 60 characters"},
            {"category": "meta", "item_text": "Meta description is compelling and 120-155 characters"},
            {"category": "meta", "item_text": "URL is clean and contains target keyword"},
            {"category": "content", "item_text": "H1 tag is present and matches search intent"},
            {"category": "content", "item_text": "Content is comprehensive and covers the topic thoroughly"},
            {"category": "content", "item_text": "Target keyword appears naturally in first 100 words"},
            {"category": "content", "item_text": "Images have descriptive ALT text"},
            {"category": "technical", "item_text": "Page loads without errors (200 status code)"},
            {"category": "technical", "item_text": "Canonical tag is set correctly"},
            {"category": "technical", "item_text": "Page is mobile-friendly"},
            {"category": "technical", "item_text": "No duplicate content issues"},
            {"category": "links", "item_text": "Internal links to related content"},
            {"category": "structured_data", "item_text": "Appropriate Schema.org markup is present"},
        ]
