"""Article plan persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class ArticlePlannerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, plan: dict) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO article_plans (website_id, idea_id, discussion_id, title, primary_topic, "
                "search_intent, audience, outline, questions, internal_links, sources, facts_to_verify, "
                "sc_evidence, source_inspiration, things_to_avoid, status) VALUES "
                "(:website_id, :idea_id, :discussion_id, :title, :primary_topic, :search_intent, :audience, "
                ":outline, :questions, :internal_links, :sources, :facts_to_verify, :sc_evidence, "
                ":source_inspiration, :things_to_avoid, :status)"
            ),
            plan,
        )
        self.db.commit()
        return result.lastrowid

    def get(self, plan_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM article_plans WHERE id = :id"), {"id": plan_id}
        ).mappings().first()
        return dict(row) if row else None

    def list(self, page: int, page_size: int, website_id: int | None, status: str | None) -> tuple[list[dict], int]:
        clauses, params = [], {"limit": page_size, "offset": (page - 1) * page_size}
        if website_id:
            clauses.append("website_id = :website_id")
            params["website_id"] = website_id
        if status:
            clauses.append("status = :status")
            params["status"] = status
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.db.execute(
            text("SELECT * FROM article_plans " + where + " ORDER BY id DESC LIMIT :limit OFFSET :offset"),
            params,
        ).mappings().all()
        total = self.db.execute(text("SELECT COUNT(*) FROM article_plans " + where), params).scalar()
        return [dict(r) for r in rows], total

    def update(self, plan_id: int, fields: dict) -> None:
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        self.db.execute(
            text(f"UPDATE article_plans SET {sets}, updated_at = datetime('now') WHERE id = :id"),
            {**fields, "id": plan_id},
        )
        self.db.commit()

    def delete(self, plan_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM article_plans WHERE id = :id"), {"id": plan_id})
        self.db.commit()
        return result.rowcount > 0
