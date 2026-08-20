"""Redirect Manager repository — CRUD, bulk operations, and check history."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.redirect_manager.schemas import RedirectCreate, RedirectUpdate


class RedirectManagerRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Redirects CRUD
    # ------------------------------------------------------------------

    def create_redirect(self, data: RedirectCreate) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO redirects (website_id, source_url, target_url, status_code, notes) "
                "VALUES (:wid, :src, :tgt, :code, :notes) "
                "RETURNING *"
            ),
            {
                "wid": data.website_id,
                "src": data.source_url,
                "tgt": data.target_url,
                "code": data.status_code.value,
                "notes": data.notes,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_redirect(self, redirect_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM redirects WHERE id = :id"),
            {"id": redirect_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_redirects_by_website(
        self, website_id: int, status: str | None = None, limit: int = 200, offset: int = 0
    ) -> list[dict]:
        query = "SELECT * FROM redirects WHERE website_id = :wid"
        params: dict = {"wid": website_id, "lim": limit, "off": offset}

        if status == "active":
            query += " AND is_active = 1"
        elif status == "inactive":
            query += " AND is_active = 0"

        query += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        rows = self.db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def count_redirects(self, website_id: int) -> int:
        return self.db.execute(
            text("SELECT COUNT(*) FROM redirects WHERE website_id = :wid"),
            {"wid": website_id},
        ).scalar()

    def update_redirect(self, redirect_id: int, data: RedirectUpdate) -> dict:
        updates = []
        params: dict = {"id": redirect_id}

        if data.target_url is not None:
            updates.append("target_url = :tgt")
            params["tgt"] = data.target_url
        if data.status_code is not None:
            updates.append("status_code = :code")
            params["code"] = data.status_code.value
        if data.is_active is not None:
            updates.append("is_active = :active")
            params["active"] = 1 if data.is_active else 0
        if data.notes is not None:
            updates.append("notes = :notes")
            params["notes"] = data.notes

        if not updates:
            return self.get_redirect(redirect_id)

        updates.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE redirects SET {', '.join(updates)} WHERE id = :id RETURNING *"),
            params,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_redirect(self, redirect_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM redirects WHERE id = :id"),
            {"id": redirect_id},
        )
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    def bulk_create(self, website_id: int, redirects: list[dict], overwrite: bool = False) -> int:
        """Bulk create redirects. Returns count inserted."""
        count = 0
        for r in redirects:
            source = r.get("source", "").strip()
            target = r.get("target", "").strip()
            code = r.get("status_code", 301)

            if not source or not target:
                continue

            # Check if exists
            existing = self.db.execute(
                text("SELECT id FROM redirects WHERE website_id = :wid AND source_url = :src"),
                {"wid": website_id, "src": source},
            ).mappings().first()

            if existing:
                if overwrite:
                    self.db.execute(
                        text(
                            "UPDATE redirects SET target_url = :tgt, status_code = :code, "
                            "updated_at = datetime('now') WHERE id = :id"
                        ),
                        {"tgt": target, "code": code, "id": existing["id"]},
                    )
                    count += 1
            else:
                self.db.execute(
                    text(
                        "INSERT INTO redirects (website_id, source_url, target_url, status_code) "
                        "VALUES (:wid, :src, :tgt, :code)"
                    ),
                    {"wid": website_id, "src": source, "tgt": target, "code": code},
                )
                count += 1

        self.db.commit()
        return count

    def get_redirect_by_source(self, website_id: int, source_url: str) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM redirects WHERE website_id = :wid AND source_url = :src"),
            {"wid": website_id, "src": source_url},
        ).mappings().first()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Check History
    # ------------------------------------------------------------------

    def add_check(self, redirect_id: int, status_code: int | None, response_time_ms: int | None,
                  final_url: str | None, error_message: str | None = None) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO redirect_checks (redirect_id, status_code, response_time_ms, final_url, error_message) "
                "VALUES (:rid, :code, :time, :url, :err) "
                "RETURNING *"
            ),
            {"rid": redirect_id, "code": status_code, "time": response_time_ms, "url": final_url, "err": error_message},
        ).mappings().one()

        # Update redirect's last check info
        self.db.execute(
            text(
                "UPDATE redirects SET last_checked_at = datetime('now'), last_status_code = :code "
                "WHERE id = :id"
            ),
            {"code": status_code, "id": redirect_id},
        )
        self.db.commit()
        return dict(row)

    def get_check_history(self, redirect_id: int, limit: int = 20) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM redirect_checks WHERE redirect_id = :rid "
                "ORDER BY checked_at DESC LIMIT :lim"
            ),
            {"rid": redirect_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, website_id: int) -> dict:
        total = self.db.execute(
            text("SELECT COUNT(*) FROM redirects WHERE website_id = :wid"),
            {"wid": website_id},
        ).scalar()

        active = self.db.execute(
            text("SELECT COUNT(*) FROM redirects WHERE website_id = :wid AND is_active = 1"),
            {"wid": website_id},
        ).scalar()

        by_status = self.db.execute(
            text(
                "SELECT status_code, COUNT(*) AS count FROM redirects "
                "WHERE website_id = :wid GROUP BY status_code"
            ),
            {"wid": website_id},
        ).mappings().all()

        chains = self.db.execute(
            text("SELECT COUNT(*) FROM redirects WHERE website_id = :wid AND chain_depth > 0"),
            {"wid": website_id},
        ).scalar()

        broken = self.db.execute(
            text(
                "SELECT COUNT(*) FROM redirects WHERE website_id = :wid "
                "AND last_status_code IS NOT NULL AND last_status_code >= 400"
            ),
            {"wid": website_id},
        ).scalar()

        avg_time = self.db.execute(
            text(
                "SELECT AVG(response_time_ms) FROM redirect_checks rc "
                "JOIN redirects r ON rc.redirect_id = r.id "
                "WHERE r.website_id = :wid AND rc.response_time_ms IS NOT NULL"
            ),
            {"wid": website_id},
        ).scalar()

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_status_code": {str(r["status_code"]): r["count"] for r in by_status},
            "chains_detected": chains,
            "broken_count": broken,
            "avg_response_time_ms": round(avg_time, 1) if avg_time else None,
        }

    def detect_chains(self, website_id: int) -> list[dict]:
        """Detect redirect chains (A→B→C where B is also a source)."""
        rows = self.db.execute(
            text(
                "SELECT r1.id, r1.source_url, r1.target_url, r1.status_code, "
                "r2.id AS chain_id, r2.target_url AS final_url "
                "FROM redirects r1 "
                "JOIN redirects r2 ON r1.target_url = r2.source_url AND r2.website_id = :wid "
                "WHERE r1.website_id = :wid AND r1.is_active = 1 AND r2.is_active = 1"
            ),
            {"wid": website_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def increment_hit_count(self, redirect_id: int) -> None:
        self.db.execute(
            text("UPDATE redirects SET hit_count = hit_count + 1 WHERE id = :id"),
            {"id": redirect_id},
        )
        self.db.commit()
