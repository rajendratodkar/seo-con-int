"""Database queries for monitoring & alerts."""
import json
from sqlalchemy import text
from sqlalchemy.orm import Session


class MonitoringRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Alert Channels -------------------------------------------------------

    def create_channel(self, name: str, channel_type: str, config: dict) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO alert_channels (name, channel_type, config) "
                "VALUES (:name, :channel_type, :config) "
                "RETURNING *"
            ),
            {"name": name, "channel_type": channel_type, "config": json.dumps(config)},
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_channel(self, channel_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM alert_channels WHERE id = :id"),
            {"id": channel_id},
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_channels(self) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM alert_channels ORDER BY created_at DESC")
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_channel(self, channel_id: int, **fields) -> dict | None:
        sets = []
        params: dict = {"id": channel_id}
        for k, v in fields.items():
            if v is not None:
                if k == "config":
                    sets.append(f"{k} = :{k}")
                    params[k] = json.dumps(v)
                else:
                    sets.append(f"{k} = :{k}")
                    params[k] = v
        if not sets:
            return self.get_channel(channel_id)
        sets.append("updated_at = datetime('now')")
        sql = f"UPDATE alert_channels SET {', '.join(sets)} WHERE id = :id RETURNING *"
        row = self.db.execute(text(sql), params).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def delete_channel(self, channel_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM alert_channels WHERE id = :id"), {"id": channel_id}
        )
        self.db.commit()
        return result.rowcount > 0

    # --- Monitoring Rules -----------------------------------------------------

    def create_rule(
        self, website_id: int, name: str, rule_type: str,
        config: dict, channel_ids: list[int], check_interval: str,
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO monitoring_rules "
                "(website_id, name, rule_type, config, channel_ids, check_interval) "
                "VALUES (:website_id, :name, :rule_type, :config, :channel_ids, :check_interval) "
                "RETURNING *"
            ),
            {
                "website_id": website_id,
                "name": name,
                "rule_type": rule_type,
                "config": json.dumps(config),
                "channel_ids": json.dumps(channel_ids),
                "check_interval": check_interval,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_rule(self, rule_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM monitoring_rules WHERE id = :id"),
            {"id": rule_id},
        ).mappings().one_or_none()
        return dict(row) if row else None

    def list_rules(self, website_id: int | None = None) -> list[dict]:
        if website_id:
            rows = self.db.execute(
                text("SELECT * FROM monitoring_rules WHERE website_id = :wid ORDER BY created_at DESC"),
                {"wid": website_id},
            ).mappings().all()
        else:
            rows = self.db.execute(
                text("SELECT * FROM monitoring_rules ORDER BY created_at DESC")
            ).mappings().all()
        return [dict(r) for r in rows]

    def list_enabled_rules(self) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM monitoring_rules WHERE enabled = 1")
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_rule(self, rule_id: int, **fields) -> dict | None:
        sets = []
        params: dict = {"id": rule_id}
        for k, v in fields.items():
            if v is not None:
                if k in ("config", "channel_ids"):
                    sets.append(f"{k} = :{k}")
                    params[k] = json.dumps(v)
                else:
                    sets.append(f"{k} = :{k}")
                    params[k] = v
        if not sets:
            return self.get_rule(rule_id)
        sets.append("updated_at = datetime('now')")
        sql = f"UPDATE monitoring_rules SET {', '.join(sets)} WHERE id = :id RETURNING *"
        row = self.db.execute(text(sql), params).mappings().one_or_none()
        self.db.commit()
        return dict(row) if row else None

    def mark_rule_checked(self, rule_id: int) -> None:
        self.db.execute(
            text("UPDATE monitoring_rules SET last_checked_at = datetime('now') WHERE id = :id"),
            {"id": rule_id},
        )
        self.db.commit()

    def delete_rule(self, rule_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM monitoring_rules WHERE id = :id"), {"id": rule_id}
        )
        self.db.commit()
        return result.rowcount > 0

    # --- Alert History --------------------------------------------------------

    def log_alert(
        self, rule_id: int, channel_id: int, severity: str,
        title: str, message: str, data: dict | None, status: str,
        error_message: str | None = None,
    ) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO alert_history "
                "(rule_id, channel_id, severity, title, message, data, status, error_message) "
                "VALUES (:rule_id, :channel_id, :severity, :title, :message, :data, :status, :error_message) "
                "RETURNING *"
            ),
            {
                "rule_id": rule_id,
                "channel_id": channel_id,
                "severity": severity,
                "title": title,
                "message": message,
                "data": json.dumps(data) if data else None,
                "status": status,
                "error_message": error_message,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def list_alert_history(
        self, rule_id: int | None = None, limit: int = 50,
    ) -> list[dict]:
        if rule_id:
            rows = self.db.execute(
                text(
                    "SELECT * FROM alert_history WHERE rule_id = :rid "
                    "ORDER BY sent_at DESC LIMIT :lim"
                ),
                {"rid": rule_id, "lim": limit},
            ).mappings().all()
        else:
            rows = self.db.execute(
                text("SELECT * FROM alert_history ORDER BY sent_at DESC LIMIT :lim"),
                {"lim": limit},
            ).mappings().all()
        return [dict(r) for r in rows]

    # --- Snapshots ------------------------------------------------------------

    def save_snapshot(
        self, website_id: int, snapshot_type: str, snapshot_date: str, data: dict,
    ) -> None:
        self.db.execute(
            text(
                "INSERT INTO monitoring_snapshots (website_id, snapshot_type, snapshot_date, data) "
                "VALUES (:wid, :stype, :sdate, :data) "
                "ON CONFLICT (website_id, snapshot_type, snapshot_date) "
                "DO UPDATE SET data = excluded.data"
            ),
            {
                "wid": website_id,
                "stype": snapshot_type,
                "sdate": snapshot_date,
                "data": json.dumps(data),
            },
        )
        self.db.commit()

    def get_previous_snapshot(
        self, website_id: int, snapshot_type: str, before_date: str,
    ) -> dict | None:
        row = self.db.execute(
            text(
                "SELECT * FROM monitoring_snapshots "
                "WHERE website_id = :wid AND snapshot_type = :stype AND snapshot_date < :before "
                "ORDER BY snapshot_date DESC LIMIT 1"
            ),
            {"wid": website_id, "stype": snapshot_type, "before": before_date},
        ).mappings().one_or_none()
        return dict(row) if row else None

    # --- Stats ----------------------------------------------------------------

    def alert_stats(self) -> dict:
        total = self.db.execute(text("SELECT COUNT(*) FROM alert_history")).scalar()
        by_status = {
            r.status: r.cnt
            for r in self.db.execute(
                text("SELECT status, COUNT(*) AS cnt FROM alert_history GROUP BY status")
            ).mappings().all()
        }
        by_severity = {
            r.severity: r.cnt
            for r in self.db.execute(
                text("SELECT severity, COUNT(*) AS cnt FROM alert_history GROUP BY severity")
            ).mappings().all()
        }
        return {"total": total, "by_status": by_status, "by_severity": by_severity}
