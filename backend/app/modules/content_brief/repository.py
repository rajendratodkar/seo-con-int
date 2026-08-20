"""Content Brief repository — storage and retrieval."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError


class ContentBriefRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Briefs CRUD
    # ------------------------------------------------------------------

    def create(self, website_id: int, target_keyword: str, primary_keyword: str) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO content_briefs (website_id, target_keyword, primary_keyword) "
                "VALUES (:wid, :kw, :pkw) RETURNING *"
            ),
            {"wid": website_id, "kw": target_keyword, "pkw": primary_keyword},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get(self, brief_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM content_briefs WHERE id = :id"),
            {"id": brief_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_by_website(self, website_id: int, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT id, website_id, target_keyword, primary_keyword, search_intent, "
                "target_word_count, status, version, created_at, updated_at "
                "FROM content_briefs WHERE website_id = :wid "
                "ORDER BY created_at DESC LIMIT :lim"
            ),
            {"wid": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update(self, brief_id: int, fields: dict) -> dict:
        set_clauses = []
        params = {"id": brief_id}
        for key, value in fields.items():
            if value is not None and key not in ("id", "created_at"):
                if isinstance(value, (list, dict)):
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = json.dumps(value)
                else:
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
        if not set_clauses:
            return self.get(brief_id) or {}
        set_clauses.append("updated_at = datetime('now')")
        sql = f"UPDATE content_briefs SET {', '.join(set_clauses)} WHERE id = :id RETURNING *"
        row = self.db.execute(text(sql), params).mappings().one()
        self.db.commit()
        return dict(row)

    def delete(self, brief_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM content_briefs WHERE id = :id"),
            {"id": brief_id},
        )
        self.db.commit()
        return result.rowcount > 0

    def next_version(self, website_id: int, target_keyword: str) -> int:
        row = self.db.execute(
            text(
                "SELECT COALESCE(MAX(version), 0) + 1 AS next_ver "
                "FROM content_briefs WHERE website_id = :wid AND target_keyword = :kw"
            ),
            {"wid": website_id, "kw": target_keyword},
        ).mappings().one()
        return row["next_ver"]

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def add_section(self, brief_id: int, section_type: str, title: str, content: str, sort_order: int = 0) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO brief_sections (brief_id, section_type, title, content, sort_order) "
                "VALUES (:bid, :stype, :title, :content, :order) RETURNING *"
            ),
            {"bid": brief_id, "stype": section_type, "title": title, "content": content, "order": sort_order},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_sections(self, brief_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM brief_sections WHERE brief_id = :bid ORDER BY sort_order"),
            {"bid": brief_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def delete_sections(self, brief_id: int) -> None:
        self.db.execute(
            text("DELETE FROM brief_sections WHERE brief_id = :bid"),
            {"bid": brief_id},
        )
        self.db.commit()

    # ------------------------------------------------------------------
    # Competitors
    # ------------------------------------------------------------------

    def add_competitor(self, brief_id: int, data: dict) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO brief_competitors "
                "(brief_id, url, title, word_count, headings, keyword_density, media_count, has_faq, has_schema) "
                "VALUES (:bid, :url, :title, :wc, :headings, :kd, :mc, :faq, :schema) RETURNING *"
            ),
            {
                "bid": brief_id,
                "url": data.get("url", ""),
                "title": data.get("title"),
                "wc": data.get("word_count"),
                "headings": json.dumps(data.get("headings", [])),
                "kd": data.get("keyword_density"),
                "mc": data.get("media_count", 0),
                "faq": 1 if data.get("has_faq") else 0,
                "schema": 1 if data.get("has_schema") else 0,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_competitors(self, brief_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM brief_competitors WHERE brief_id = :bid ORDER BY word_count DESC"),
            {"bid": brief_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def delete_competitors(self, brief_id: int) -> None:
        self.db.execute(
            text("DELETE FROM brief_competitors WHERE brief_id = :bid"),
            {"bid": brief_id},
        )
        self.db.commit()
