"""Content ideas: generation from real data, scoring, validation (plan §17).

Generators are data-based only (Rule 5): every idea carries the evidence that
produced it. AI is never the source of an idea's "truth".
"""
from sqlalchemy.orm import Session

from app.modules.content_ideas.repository import ContentIdeasRepository

STATUSES = ("draft", "validated", "approved", "rejected")


class ContentIdeasService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContentIdeasRepository(db)

    # -- generation -------------------------------------------------------------
    def generate(self, website_id: int) -> list[dict]:
        """Produce candidate ideas from Search Console gaps + research questions."""
        ideas = self._from_search_console(website_id) + self._from_research_questions()
        created = []
        for idea in ideas:
            if self.repo.title_exists(idea["title"]):
                continue
            idea_id = self.repo.create(idea)
            created.append(self.repo.get(idea_id))
        return created

    def _from_search_console(self, website_id: int) -> list[dict]:
        """Queries with impressions but no dedicated page content (data-based)."""
        from sqlalchemy import text

        rows = self.db.execute(
            text(
                "SELECT query, SUM(impressions) AS impressions, SUM(clicks) AS clicks, "
                "AVG(position) AS avg_position FROM search_console_data "
                "WHERE website_id = :website_id AND query IS NOT NULL "
                "AND date >= date('now', '-90 days') "
                "GROUP BY query HAVING impressions >= 100 ORDER BY impressions DESC LIMIT 25"
            ),
            {"website_id": website_id},
        ).mappings().all()
        ideas = []
        for row in rows:
            score = min(1.0, row["impressions"] / 10000)
            if 4 <= row["avg_position"] <= 20:
                score = min(1.0, score + 0.2)  # already ranking — easier win
            ideas.append({
                "website_id": website_id,
                "source_type": "search_console",
                "source_id": None,
                "title": row["query"].capitalize(),
                "description": (
                    f"Search Console evidence: {row['impressions']:,} impressions, "
                    f"{row['clicks']:,} clicks, avg position {row['avg_position']:.1f} in the last 90 days."
                ),
                "status": "draft",
                "score": round(score, 3),
            })
        return ideas

    def _from_research_questions(self) -> list[dict]:
        """Unanswered questions found in research sources."""
        from sqlalchemy import text

        rows = self.db.execute(
            text(
                "SELECT q.id, q.question, s.title AS source_title FROM research_questions q "
                "LEFT JOIN research_sources s ON s.id = q.source_id "
                "WHERE q.answered = 0 ORDER BY q.id DESC LIMIT 25"
            )
        ).mappings().all()
        return [
            {
                "website_id": None,
                "source_type": "research",
                "source_id": row["id"],
                "title": row["question"],
                "description": f"Unanswered question found while researching: {row['source_title'] or 'a source'}.",
                "status": "draft",
                "score": 0.4,
            }
            for row in rows
        ]

    # -- validation (plan §17: validate before approving) ------------------------
    def validate(self, idea_id: int) -> dict:
        idea = self.repo.get(idea_id)
        if idea is None:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("idea.not_found", f"Content idea {idea_id} does not exist")
        checks = {
            "has_evidence": bool(idea["description"]),
            "not_duplicate": not self.repo.title_exists(idea["title"], exclude_id=idea_id),
            "has_source": idea["source_type"] is not None,
        }
        if all(checks.values()):
            self.repo.update_status(idea_id, "validated")
        idea = self.repo.get(idea_id)
        idea["validation"] = checks
        return idea

    # -- CRUD --------------------------------------------------------------------
    def create_manual(self, website_id: int | None, title: str, description: str | None) -> dict:
        from app.core.exceptions import ConflictError
        if self.repo.title_exists(title):
            raise ConflictError("idea.duplicate", f"An idea with this title already exists: {title}")
        idea_id = self.repo.create({
            "website_id": website_id, "source_type": "manual", "source_id": None,
            "title": title, "description": description, "status": "draft", "score": None,
        })
        return self.repo.get(idea_id)

    def list(self, page: int, page_size: int, website_id: int | None, status: str | None) -> tuple[list, int]:
        return self.repo.list(page, page_size, website_id, status)

    def get(self, idea_id: int) -> dict | None:
        return self.repo.get(idea_id)

    def set_status(self, idea_id: int, status: str) -> dict:
        from app.core.exceptions import AppError, NotFoundError
        if status not in STATUSES:
            raise AppError("idea.invalid_status", f"status must be one of {STATUSES}")
        if self.repo.get(idea_id) is None:
            raise NotFoundError("idea.not_found", f"Content idea {idea_id} does not exist")
        self.repo.update_status(idea_id, status)
        return self.repo.get(idea_id)

    def delete(self, idea_id: int) -> bool:
        return self.repo.delete(idea_id)
