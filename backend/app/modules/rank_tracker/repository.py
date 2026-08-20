"""Rank Tracker repository — CRUD, snapshots, and trends."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.rank_tracker.schemas import TrackedKeywordCreate, TrackedKeywordUpdate


class RankTrackerRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Tracked Keywords CRUD
    # ------------------------------------------------------------------

    def create_keyword(self, data: TrackedKeywordCreate) -> dict:
        row = self.db.execute(
            text(
                "INSERT INTO tracked_keywords (website_id, keyword, target_url, group_name, notes) "
                "VALUES (:wid, :kw, :url, :group, :notes) "
                "RETURNING *"
            ),
            {
                "wid": data.website_id,
                "kw": data.keyword,
                "url": data.target_url,
                "group": data.group_name,
                "notes": data.notes,
            },
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def get_keyword(self, keyword_id: int) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM tracked_keywords WHERE id = :id"),
            {"id": keyword_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_keywords_by_website(self, website_id: int, limit: int = 200) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT tk.*, "
                "rs.position AS current_position, "
                "rs_prev.position AS previous_position, "
                "CASE WHEN rs.position IS NOT NULL AND rs_prev.position IS NOT NULL "
                "    THEN rs_prev.position - rs.position ELSE NULL END AS position_change "
                "FROM tracked_keywords tk "
                "LEFT JOIN rank_snapshots rs ON tk.id = rs.keyword_id "
                "    AND rs.snapshot_date = (SELECT MAX(snapshot_date) FROM rank_snapshots WHERE keyword_id = tk.id) "
                "LEFT JOIN rank_snapshots rs_prev ON tk.id = rs_prev.keyword_id "
                "    AND rs_prev.snapshot_date = (SELECT MAX(snapshot_date) FROM rank_snapshots WHERE keyword_id = tk.id AND snapshot_date < rs.snapshot_date) "
                "WHERE tk.website_id = :wid "
                "ORDER BY rs.position ASC NULLS LAST"
            ),
            {"wid": website_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_keyword(self, keyword_id: int, data: TrackedKeywordUpdate) -> dict:
        updates = []
        params: dict = {"id": keyword_id}

        if data.target_url is not None:
            updates.append("target_url = :url")
            params["url"] = data.target_url
        if data.group_name is not None:
            updates.append("group_name = :group")
            params["group"] = data.group_name
        if data.notes is not None:
            updates.append("notes = :notes")
            params["notes"] = data.notes
        if data.is_active is not None:
            updates.append("is_active = :active")
            params["active"] = 1 if data.is_active else 0

        if not updates:
            return self.get_keyword(keyword_id)

        updates.append("updated_at = datetime('now')")
        row = self.db.execute(
            text(f"UPDATE tracked_keywords SET {', '.join(updates)} WHERE id = :id RETURNING *"),
            params,
        ).mappings().one()
        self.db.commit()
        return dict(row)

    def delete_keyword(self, keyword_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM tracked_keywords WHERE id = :id"),
            {"id": keyword_id},
        )
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def add_snapshot(self, data: dict) -> dict:
        # Get previous position
        prev = self.db.execute(
            text(
                "SELECT position FROM rank_snapshots "
                "WHERE keyword_id = :kid ORDER BY snapshot_date DESC LIMIT 1"
            ),
            {"kid": data["keyword_id"]},
        ).mappings().first()

        previous_position = prev["position"] if prev else None
        position = data.get("position")
        change = None
        if position is not None and previous_position is not None:
            change = previous_position - position  # positive = improvement

        row = self.db.execute(
            text(
                "INSERT INTO rank_snapshots (keyword_id, position, previous_position, change, "
                "search_volume, clicks, impressions, ctr, url, search_engine, country, device, snapshot_date) "
                "VALUES (:kid, :pos, :prev, :chg, :vol, :clicks, :imp, :ctr, :url, :engine, :country, :device, :date) "
                "RETURNING *"
            ),
            {
                "kid": data["keyword_id"],
                "pos": position,
                "prev": previous_position,
                "chg": change,
                "vol": data.get("search_volume"),
                "clicks": data.get("clicks"),
                "imp": data.get("impressions"),
                "ctr": data.get("ctr"),
                "url": data.get("url"),
                "engine": data.get("search_engine", "google"),
                "country": data.get("country", "us"),
                "device": data.get("device", "desktop"),
                "date": data["snapshot_date"],
            },
        ).mappings().one()
        self.db.commit()

        # Create alert if significant change
        if change is not None and abs(change) >= 3:
            alert_type = "position_change"
            if change > 0:
                message = f"'{self._get_keyword_text(data['keyword_id'])}' improved from #{previous_position} to #{position} (+{change})"
            else:
                message = f"'{self._get_keyword_text(data['keyword_id'])}' dropped from #{previous_position} to #{position} ({change})"

            self.db.execute(
                text(
                    "INSERT INTO rank_alerts (keyword_id, alert_type, old_position, new_position, change, message) "
                    "VALUES (:kid, :type, :old, :new, :chg, :msg)"
                ),
                {
                    "kid": data["keyword_id"],
                    "type": alert_type,
                    "old": previous_position,
                    "new": position,
                    "chg": change,
                    "msg": message,
                },
            )
            self.db.commit()

        return dict(row)

    def _get_keyword_text(self, keyword_id: int) -> str:
        row = self.db.execute(
            text("SELECT keyword FROM tracked_keywords WHERE id = :id"),
            {"id": keyword_id},
        ).mappings().first()
        return row["keyword"] if row else "Unknown"

    def get_snapshots(self, keyword_id: int, limit: int = 90) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT * FROM rank_snapshots WHERE keyword_id = :kid "
                "ORDER BY snapshot_date DESC LIMIT :lim"
            ),
            {"kid": keyword_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_snapshots_by_website(self, website_id: int, days: int = 30) -> list[dict]:
        rows = self.db.execute(
            text(
                "SELECT rs.*, tk.keyword FROM rank_snapshots rs "
                "JOIN tracked_keywords tk ON rs.keyword_id = tk.id "
                "WHERE tk.website_id = :wid AND rs.snapshot_date >= date('now', :days) "
                "ORDER BY rs.snapshot_date DESC"
            ),
            {"wid": website_id, "days": f"-{days} days"},
        ).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def get_alerts(self, website_id: int, unread_only: bool = False, limit: int = 50) -> list[dict]:
        query = (
            "SELECT ra.*, tk.keyword FROM rank_alerts ra "
            "JOIN tracked_keywords tk ON ra.keyword_id = tk.id "
            "WHERE tk.website_id = :wid"
        )
        if unread_only:
            query += " AND ra.is_read = 0"
        query += " ORDER BY ra.created_at DESC LIMIT :lim"

        rows = self.db.execute(text(query), {"wid": website_id, "lim": limit}).mappings().all()
        return [dict(r) for r in rows]

    def mark_alert_read(self, alert_id: int) -> bool:
        result = self.db.execute(
            text("UPDATE rank_alerts SET is_read = 1 WHERE id = :id"),
            {"id": alert_id},
        )
        self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, website_id: int) -> dict:
        total = self.db.execute(
            text("SELECT COUNT(*) FROM tracked_keywords WHERE website_id = :wid"),
            {"wid": website_id},
        ).scalar()

        active = self.db.execute(
            text("SELECT COUNT(*) FROM tracked_keywords WHERE website_id = :wid AND is_active = 1"),
            {"wid": website_id},
        ).scalar()

        # Get latest positions
        latest_positions = self.db.execute(
            text(
                "SELECT tk.keyword, rs.position FROM tracked_keywords tk "
                "JOIN rank_snapshots rs ON tk.id = rs.keyword_id "
                "AND rs.snapshot_date = (SELECT MAX(snapshot_date) FROM rank_snapshots WHERE keyword_id = tk.id) "
                "WHERE tk.website_id = :wid AND rs.position IS NOT NULL"
            ),
            {"wid": website_id},
        ).mappings().all()

        positions = [r["position"] for r in latest_positions]
        avg_pos = sum(positions) / len(positions) if positions else None

        top_10 = sum(1 for p in positions if p <= 10)
        top_20 = sum(1 for p in positions if p <= 20)
        top_50 = sum(1 for p in positions if p <= 50)

        # Position changes
        improved = self.db.execute(
            text(
                "SELECT COUNT(*) FROM rank_snapshots rs "
                "JOIN tracked_keywords tk ON rs.keyword_id = tk.id "
                "WHERE tk.website_id = :wid AND rs.change > 0 "
                "AND rs.snapshot_date = (SELECT MAX(snapshot_date) FROM rank_snapshots WHERE keyword_id = rs.keyword_id)"
            ),
            {"wid": website_id},
        ).scalar()

        dropped = self.db.execute(
            text(
                "SELECT COUNT(*) FROM rank_snapshots rs "
                "JOIN tracked_keywords tk ON rs.keyword_id = tk.id "
                "WHERE tk.website_id = :wid AND rs.change < 0 "
                "AND rs.snapshot_date = (SELECT MAX(snapshot_date) FROM rank_snapshots WHERE keyword_id = rs.keyword_id)"
            ),
            {"wid": website_id},
        ).scalar()

        unchanged = total - improved - dropped if total else 0

        # Best keyword
        best = self.db.execute(
            text(
                "SELECT tk.keyword, rs.position FROM tracked_keywords tk "
                "JOIN rank_snapshots rs ON tk.id = rs.keyword_id "
                "WHERE tk.website_id = :wid AND rs.position IS NOT NULL "
                "ORDER BY rs.position ASC LIMIT 1"
            ),
            {"wid": website_id},
        ).mappings().first()

        return {
            "total_keywords": total,
            "active_keywords": active,
            "avg_position": round(avg_pos, 1) if avg_pos else None,
            "top_10_count": top_10,
            "top_20_count": top_20,
            "top_50_count": top_50,
            "position_improved": improved,
            "position_dropped": dropped,
            "position_unchanged": unchanged,
            "best_keyword": best["keyword"] if best else None,
            "best_position": best["position"] if best else None,
        }

    def get_keyword_trend(self, keyword_id: int, days: int = 30) -> list[dict]:
        """Get position trend for a keyword."""
        rows = self.db.execute(
            text(
                "SELECT snapshot_date, position, clicks, impressions, ctr "
                "FROM rank_snapshots WHERE keyword_id = :kid "
                "AND snapshot_date >= date('now', :days) "
                "ORDER BY snapshot_date ASC"
            ),
            {"kid": keyword_id, "days": f"-{days} days"},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_website_trends(self, website_id: int, days: int = 30) -> list[dict]:
        """Get trends for all keywords in a website."""
        keywords = self.db.execute(
            text(
                "SELECT id, keyword FROM tracked_keywords "
                "WHERE website_id = :wid AND is_active = 1"
            ),
            {"wid": website_id},
        ).mappings().all()

        trends = []
        for kw in keywords:
            data_points = self.get_keyword_trend(kw["id"], days)
            if len(data_points) >= 2:
                first_pos = data_points[0]["position"]
                last_pos = data_points[-1]["position"]
                if first_pos and last_pos:
                    if last_pos < first_pos:
                        trend = "improving"
                    elif last_pos > first_pos:
                        trend = "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            current = data_points[-1]["position"] if data_points else None
            trends.append({
                "keyword_id": kw["id"],
                "keyword": kw["keyword"],
                "current_position": current,
                "trend": trend,
                "data_points": data_points,
            })

        # Sort by current position
        trends.sort(key=lambda x: x["current_position"] or 999)
        return trends
