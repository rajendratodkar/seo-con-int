"""Research sources persistence (SQL only — Rule 3: no business logic here)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class ResearchRepository:
    def __init__(self, db: Session):
        self.db = db

    # -- sources ---------------------------------------------------------------
    def create_source(
        self,
        source_type: str,
        url: str | None = None,
        title: str | None = None,
        website_id: int | None = None,
        raw_data: str | None = None,
        availability_status: str = "pending",
    ) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO research_sources "
                "(website_id, source_type, url, title, availability_status, raw_data) "
                "VALUES (:website_id, :source_type, :url, :title, :availability_status, :raw_data)"
            ),
            {
                "website_id": website_id,
                "source_type": source_type,
                "url": url,
                "title": title,
                "availability_status": availability_status,
                "raw_data": raw_data,
            },
        )
        self.db.commit()
        return result.lastrowid

    def update_extraction(
        self, source_id: int, extraction_status: str, availability_status: str | None = None,
        title: str | None = None, raw_data: str | None = None, error_message: str | None = None,
    ) -> None:
        self.db.execute(
            text(
                "UPDATE research_sources SET extraction_status = :extraction_status, "
                "availability_status = COALESCE(:availability_status, availability_status), "
                "title = COALESCE(:title, title), raw_data = COALESCE(:raw_data, raw_data), "
                "error_message = :error_message, updated_at = datetime('now') WHERE id = :id"
            ),
            {
                "id": source_id,
                "extraction_status": extraction_status,
                "availability_status": availability_status,
                "title": title,
                "raw_data": raw_data,
                "error_message": error_message,
            },
        )
        self.db.commit()

    def get_source(self, source_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM research_sources WHERE id = :id"), {"id": source_id}
        ).mappings().first()
        return dict(row) if row else None

    def list_sources(self, page: int, page_size: int, source_type: str | None = None) -> tuple[list[dict], int]:
        where = "WHERE source_type = :source_type" if source_type else ""
        params: dict = {"limit": page_size, "offset": (page - 1) * page_size}
        if source_type:
            params["source_type"] = source_type
        rows = self.db.execute(
            text(
                "SELECT * FROM research_sources " + where +
                " ORDER BY id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
        total = self.db.execute(
            text("SELECT COUNT(*) FROM research_sources " + where), params
        ).scalar()
        return [dict(r) for r in rows], total

    def delete_source(self, source_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM research_sources WHERE id = :id"), {"id": source_id}
        )
        self.db.commit()
        return result.rowcount > 0

    # -- topics / claims / questions -------------------------------------------
    def add_topics(self, source_id: int, topics: list[tuple[str, float]]) -> None:
        for topic, importance in topics:
            self.db.execute(
                text("INSERT INTO research_topics (source_id, topic, importance) VALUES (:s, :t, :i)"),
                {"s": source_id, "t": topic, "i": importance},
            )
        self.db.commit()

    def add_claims(self, source_id: int, claims: list[dict]) -> None:
        for c in claims:
            self.db.execute(
                text(
                    "INSERT INTO research_claims (source_id, claim_text, evidence, confidence) "
                    "VALUES (:s, :claim_text, :evidence, :confidence)"
                ),
                {"s": source_id, **c},
            )
        self.db.commit()

    def add_questions(self, source_id: int | None, questions: list[str]) -> None:
        for q in questions:
            self.db.execute(
                text("INSERT INTO research_questions (source_id, question) VALUES (:s, :q)"),
                {"s": source_id, "q": q},
            )
        self.db.commit()

    def set_question_answered(self, question_id: int, answered: bool) -> None:
        self.db.execute(
            text("UPDATE research_questions SET answered = :a WHERE id = :id"),
            {"id": question_id, "a": 1 if answered else 0},
        )
        self.db.commit()

    def list_topics(self, source_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM research_topics WHERE source_id = :s ORDER BY importance DESC"), {"s": source_id}
        ).mappings().all()
        return [dict(r) for r in rows]

    def list_claims(self, source_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM research_claims WHERE source_id = :s ORDER BY id"), {"s": source_id}
        ).mappings().all()
        return [dict(r) for r in rows]

    def list_questions(self, source_id: int | None = None) -> list[dict]:
        where = "WHERE source_id = :s" if source_id else ""
        params = {"s": source_id} if source_id else {}
        rows = self.db.execute(
            text("SELECT * FROM research_questions " + where + " ORDER BY id DESC"), params
        ).mappings().all()
        return [dict(r) for r in rows]
