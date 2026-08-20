"""Database queries for SEO checklist."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class ChecklistRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_tables(self) -> None:
        """Create checklist tables if they don't exist."""
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS seo_checklists ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE, "
            "page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE, "
            "status TEXT NOT NULL DEFAULT 'in_progress', "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "UNIQUE (website_id, page_id))"
        ))
        self.db.execute(text(
            "CREATE TABLE IF NOT EXISTS seo_checklist_items ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "checklist_id INTEGER NOT NULL REFERENCES seo_checklists(id) ON DELETE CASCADE, "
            "category TEXT NOT NULL, "
            "item_text TEXT NOT NULL, "
            "status TEXT NOT NULL DEFAULT 'todo', "
            "finding_id INTEGER REFERENCES seo_findings(id) ON DELETE SET NULL, "
            "notes TEXT, "
            "completed_at TEXT, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')))"
        ))
        self.db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_checklist_items_checklist ON seo_checklist_items(checklist_id)"
        ))
        self.db.commit()

    def get_or_create_checklist(self, website_id: int, page_id: int) -> dict:
        row = self.db.execute(
            text("SELECT * FROM seo_checklists WHERE website_id = :wid AND page_id = :pid"),
            {"wid": website_id, "pid": page_id},
        ).mappings().one_or_none()
        if row:
            return dict(row)
        row = self.db.execute(
            text(
                "INSERT INTO seo_checklists (website_id, page_id) VALUES (:wid, :pid) RETURNING *"
            ),
            {"wid": website_id, "pid": page_id},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def list_checklists(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM seo_checklists WHERE website_id = :wid ORDER BY updated_at DESC"),
            {"wid": website_id},
        ).mappings().all()
        result = []
        for r in rows:
            d = dict(r)
            stats = self._item_stats(d["id"])
            d.update(stats)
            result.append(d)
        return result

    def get_checklist(self, checklist_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM seo_checklists WHERE id = :id"), {"id": checklist_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def get_items(self, checklist_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM seo_checklist_items WHERE checklist_id = :cid ORDER BY category, created_at"),
            {"cid": checklist_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def add_item(self, checklist_id: int, category: str, item_text: str, notes: str | None = None, finding_id: int | None = None) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO seo_checklist_items (checklist_id, category, item_text, notes, finding_id) "
                "VALUES (:cid, :cat, :text, :notes, :fid) RETURNING *"
            ),
            {"cid": checklist_id, "cat": category, "text": item_text, "notes": notes, "fid": finding_id},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def bulk_add_items(self, checklist_id: int, items: list[dict]) -> int:
        count = 0
        for item in items:
            try:
                self.add_item(
                    checklist_id, item["category"], item["item_text"],
                    item.get("notes"), item.get("finding_id"),
                )
                count += 1
            except Exception:
                pass
        return count

    def update_item(self, item_id: int, **fields) -> dict | None:
        sets, params = [], {"id": item_id}
        for k, v in fields.items():
            if v is not None:
                sets.append(f"{k} = :{k}")
                params[k] = v
        if "status" in fields and fields["status"] == "done":
            sets.append("completed_at = datetime('now')")
        if not sets:
            return None
        row = self.db.execute(
            text(f"UPDATE seo_checklist_items SET {', '.join(sets)} WHERE id = :id RETURNING *"), params
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_item(self, item_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM seo_checklist_items WHERE id = :id"), {"id": item_id})
        self.db.commit()
        return result.rowcount > 0

    def update_checklist_status(self, checklist_id: int, status: str) -> dict | None:
        row = self.db.execute(
            text("UPDATE seo_checklists SET status = :s, updated_at = datetime('now') WHERE id = :id RETURNING *"),
            {"id": checklist_id, "s": status},
        ).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_checklist(self, checklist_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM seo_checklists WHERE id = :id"), {"id": checklist_id})
        self.db.commit()
        return result.rowcount > 0

    def _item_stats(self, checklist_id: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done "
                "FROM seo_checklist_items WHERE checklist_id = :cid"
            ),
            {"cid": checklist_id},
        ).mappings().one()
        total = row.total or 0
        done = row.done or 0
        return {
            "total_items": total,
            "done_items": done,
            "progress_pct": round((done / total * 100) if total > 0 else 0, 1),
        }
