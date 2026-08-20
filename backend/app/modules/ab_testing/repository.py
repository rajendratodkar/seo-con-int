"""Database queries for A/B testing."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class ABTestRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Tests ----------------------------------------------------------------

    def create_test(
        self, website_id: int, page_id: int, name: str, element: str,
        min_duration_days: int,
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO ab_tests (website_id, page_id, name, element, min_duration_days) "
                "VALUES (:wid, :pid, :name, :element, :min_days) "
                "RETURNING *"
            ),
            {"wid": website_id, "pid": page_id, "name": name, "element": element, "min_days": min_duration_days},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_test(self, test_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM ab_tests WHERE id = :id"), {"id": test_id}
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_tests(self, website_id: int | None = None, status: str | None = None) -> list[dict]:
        conditions = []
        params: dict = {}
        if website_id:
            conditions.append("website_id = :wid")
            params["wid"] = website_id
        if status:
            conditions.append("status = :status")
            params["status"] = status
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self.db.execute(
            text(f"SELECT * FROM ab_tests {where} ORDER BY created_at DESC"), params
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_test(self, test_id: int, **fields) -> dict | None:
        sets = []
        params: dict = {"id": test_id}
        for k, v in fields.items():
            if v is not None:
                if k == "result_summary":
                    sets.append(f"{k} = :{k}")
                    params[k] = json.dumps(v)
                else:
                    sets.append(f"{k} = :{k}")
                    params[k] = v
        if not sets:
            return self.get_test(test_id)
        sets.append("updated_at = datetime('now')")
        sql = f"UPDATE ab_tests SET {', '.join(sets)} WHERE id = :id RETURNING *"
        row = self.db.execute(text(sql), params).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_test(self, test_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM ab_tests WHERE id = :id"), {"id": test_id})
        self.db.commit()
        return result.rowcount > 0

    # --- Variants -------------------------------------------------------------

    def create_variant(
        self, test_id: int, variant_type: str, title: str | None, description: str | None,
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO ab_variants (test_id, variant_type, title, description) "
                "VALUES (:tid, :vtype, :title, :desc) "
                "RETURNING *"
            ),
            {"tid": test_id, "vtype": variant_type, "title": title, "desc": description},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_variant(self, test_id: int, variant_type: str) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM ab_variants WHERE test_id = :tid AND variant_type = :vtype"),
            {"tid": test_id, "vtype": variant_type},
        ).mappings().one_or_none()
        return dict(row) if row else None

    def get_variants(self, test_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM ab_variants WHERE test_id = :tid"), {"tid": test_id}
        ).mappings().all()
        return [dict(r) for r in rows]

    # --- Daily Snapshots ------------------------------------------------------

    def upsert_snapshot(
        self, test_id: int, variant_id: int, date: str,
        clicks: int, impressions: int, ctr: float, position: float,
    ) -> None:
        self.db.execute(
            text(
                "INSERT INTO ab_daily_snapshots (test_id, variant_id, date, clicks, impressions, ctr, position) "
                "VALUES (:tid, :vid, :date, :clicks, :imp, :ctr, :pos) "
                "ON CONFLICT (test_id, variant_id, date) DO UPDATE SET "
                "clicks = excluded.clicks, impressions = excluded.impressions, "
                "ctr = excluded.ctr, position = excluded.position"
            ),
            {"tid": test_id, "vid": variant_id, "date": date,
             "clicks": clicks, "imp": impressions, "ctr": ctr, "pos": position},
        )
        self.db.commit()

    def get_snapshots(self, test_id: int, variant_id: int) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM ab_daily_snapshots "
                "WHERE test_id = :tid AND variant_id = :vid ORDER BY date"
            ),
            {"tid": test_id, "vid": variant_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_aggregated_metrics(self, test_id: int, variant_id: int) -> dict:
        row = self.db.execute(
            text(
                "SELECT SUM(clicks) AS total_clicks, SUM(impressions) AS total_impressions, "
                "AVG(ctr) AS avg_ctr, AVG(position) AS avg_position, COUNT(*) AS days "
                "FROM ab_daily_snapshots WHERE test_id = :tid AND variant_id = :vid"
            ),
            {"tid": test_id, "vid": variant_id},
        ).mappings().one_or_none()
        return dict(row) if row else {"total_clicks": 0, "total_impressions": 0, "avg_ctr": 0, "avg_position": 0, "days": 0}
