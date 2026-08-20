"""Article planner: idea -> brief (outline, questions, evidence, links).

The brief is assembled from DATA (Search Console, research claims, page
inventory). AI may suggest an outline but that suggestion is labeled and never
auto-trusted (Rule 5).
"""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.article_planner.repository import ArticlePlannerRepository

STATUSES = ("draft", "brief_ready", "drafting", "approved")


class ArticlePlannerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ArticlePlannerRepository(db)

    def create_from_idea(self, idea_id: int, website_id: int | None = None) -> dict:
        idea = self.db.execute(
            text("SELECT * FROM content_ideas WHERE id = :id"), {"id": idea_id}
        ).mappings().first()
        if idea is None:
            raise NotFoundError("idea.not_found", f"Content idea {idea_id} does not exist")
        website_id = website_id or idea["website_id"]
        evidence = self._gather_evidence(website_id, idea["title"])
        plan_id = self.repo.create({
            "website_id": website_id,
            "idea_id": idea_id,
            "discussion_id": None,
            "title": idea["title"],
            "primary_topic": idea["title"],
            "search_intent": self._infer_intent(idea["title"]),
            "audience": None,
            "outline": json.dumps([]),
            "questions": json.dumps(evidence["questions"]),
            "internal_links": json.dumps([]),
            "sources": json.dumps(evidence["sources"]),
            "facts_to_verify": json.dumps(evidence["facts_to_verify"]),
            "sc_evidence": json.dumps(evidence["sc_evidence"]),
            "source_inspiration": json.dumps([idea["source_id"]] if idea["source_id"] else []),
            "things_to_avoid": json.dumps([]),
            "status": "draft",
        })
        return self.repo.get(plan_id)

    def create_manual(self, website_id: int | None, title: str, audience: str | None = None) -> dict:
        plan_id = self.repo.create({
            "website_id": website_id, "idea_id": None, "discussion_id": None,
            "title": title, "primary_topic": title,
            "search_intent": self._infer_intent(title), "audience": audience,
            "outline": json.dumps([]), "questions": json.dumps([]), "internal_links": json.dumps([]),
            "sources": json.dumps([]), "facts_to_verify": json.dumps([]), "sc_evidence": json.dumps([]),
            "source_inspiration": json.dumps([]), "things_to_avoid": json.dumps([]),
            "status": "draft",
        })
        return self.repo.get(plan_id)

    def _gather_evidence(self, website_id: int | None, title: str) -> dict:
        """Data-based evidence bundle for the brief (never fabricated)."""
        evidence = {"questions": [], "sources": [], "facts_to_verify": [], "sc_evidence": []}
        # Unverified claims from research = facts the article must check
        rows = self.db.execute(
            text(
                "SELECT c.claim_text, c.evidence FROM research_claims c "
                "JOIN research_sources s ON s.id = c.source_id "
                "WHERE c.verified = 0 ORDER BY c.id DESC LIMIT 10"
            )
        ).mappings().all()
        evidence["facts_to_verify"] = [dict(r) for r in rows]
        evidence["sources"] = [
            dict(r) for r in self.db.execute(
                text("SELECT id, title, url FROM research_sources WHERE availability_status = 'full' ORDER BY id DESC LIMIT 10")
            ).mappings().all()
        ]
        if website_id:
            rows = self.db.execute(
                text(
                    "SELECT query, SUM(impressions) AS impressions, AVG(position) AS avg_position "
                    "FROM search_console_data WHERE website_id = :w AND query LIKE :q "
                    "AND date >= date('now', '-90 days') GROUP BY query ORDER BY impressions DESC LIMIT 10"
                ),
                {"w": website_id, "q": f"%{title.split()[0]}%"} if title.split() else {"w": website_id, "q": "%%"},
            ).mappings().all()
            evidence["sc_evidence"] = [dict(r) for r in rows]
        return evidence

    @staticmethod
    def _infer_intent(title: str) -> str:
        lowered = title.lower()
        if any(w in lowered for w in ("buy", "price", "best", "top", "vs", "review")):
            return "commercial"
        if any(w in lowered for w in ("how", "what", "why", "guide", "learn", "?")):
            return "informational"
        return "informational"

    def update_brief(self, plan_id: int, fields: dict) -> dict:
        if self.repo.get(plan_id) is None:
            raise NotFoundError("plan.not_found", f"Article plan {plan_id} does not exist")
        allowed = {"title", "primary_topic", "search_intent", "audience", "outline",
                   "questions", "internal_links", "sources", "facts_to_verify", "things_to_avoid"}
        clean = {}
        for key, value in fields.items():
            if key not in allowed:
                continue
            clean[key] = value if isinstance(value, (str, type(None))) else json.dumps(value)
        if clean:
            self.repo.update(plan_id, clean)
        return self.repo.get(plan_id)

    def mark_brief_ready(self, plan_id: int) -> dict:
        plan = self.update_brief(plan_id, {})
        self.repo.update(plan_id, {"status": "brief_ready"})
        return self.repo.get(plan_id)

    def set_status(self, plan_id: int, status: str) -> dict:
        if status not in STATUSES:
            from app.core.exceptions import AppError
            raise AppError("plan.invalid_status", f"status must be one of {STATUSES}")
        if self.repo.get(plan_id) is None:
            raise NotFoundError("plan.not_found", f"Article plan {plan_id} does not exist")
        self.repo.update(plan_id, {"status": status})
        return self.repo.get(plan_id)

    def get(self, plan_id: int) -> dict:
        plan = self.repo.get(plan_id)
        if plan is None:
            raise NotFoundError("plan.not_found", f"Article plan {plan_id} does not exist")
        return plan

    def list(self, page: int, page_size: int, website_id: int | None, status: str | None) -> tuple[list, int]:
        return self.repo.list(page, page_size, website_id, status)

    def delete(self, plan_id: int) -> bool:
        return self.repo.delete(plan_id)
