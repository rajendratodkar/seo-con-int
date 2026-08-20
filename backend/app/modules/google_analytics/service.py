"""Google Analytics orchestration: property discovery, connection, sync, summaries.

Reuses the Google OAuth token stored by the Search Console flow (settings key
`google_oauth`); refreshes automatically on 401 when a refresh token exists.
Rule 7: raw runReport responses are archived under data/raw/ga/.
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.exceptions import AppError, NotFoundError, UpstreamError
from app.integrations.ga.client import GoogleAnalyticsClient
from app.modules.google_analytics.repository import GoogleAnalyticsRepository
from app.modules.search_console import oauth

TOKEN_KEY = "google_oauth"
METRIC_FIELDS = {"sessions": "sessions", "activeUsers": "active_users", "screenPageViews": "pageviews"}


class GoogleAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GoogleAnalyticsRepository(db)

    # --- OAuth token reuse ---------------------------------------------------------
    def _tokens(self) -> dict:
        raw = self.db.execute(
            text("SELECT value FROM settings WHERE key = :k"), {"k": TOKEN_KEY}
        ).scalar_one_or_none()
        if not raw:
            raise AppError(
                "ga.not_connected",
                "Connect a Google account first (Search Console page → Connect Google).",
            )
        return json.loads(raw)

    async def _call(self, method: str, *args, **kwargs):
        """Call the GA API once; on 401, refresh the token and retry once."""
        tokens = self._tokens()
        client = GoogleAnalyticsClient(tokens["access_token"])
        try:
            return await getattr(client, method)(*args, **kwargs)
        except UpstreamError as err:
            if err.details.get("status_code") != 401 or not tokens.get("refresh_token"):
                raise
            refreshed = await oauth.refresh_token(tokens["refresh_token"])
            tokens = {**tokens, **refreshed, "refresh_token": tokens["refresh_token"]}
            self._save_tokens(tokens)
            client = GoogleAnalyticsClient(tokens["access_token"])
            return await getattr(client, method)(*args, **kwargs)

    def _save_tokens(self, tokens: dict) -> None:
        self.db.execute(
            text(
                "INSERT INTO settings (key, value) VALUES (:k, :v) "
                "ON CONFLICT(key) DO UPDATE SET value = :v, updated_at = datetime('now')"
            ),
            {"k": TOKEN_KEY, "v": json.dumps(tokens)},
        )
        self.db.commit()

    # --- properties & connections -----------------------------------------------------
    async def list_properties(self) -> list[dict]:
        return await self._call("list_properties")

    def connect(self, website_id: int, property_id: str, property_name: str | None) -> dict:
        self._require_website(website_id)
        return self.repo.upsert_connection(website_id, str(property_id), property_name)

    def get_connection(self, website_id: int) -> dict | None:
        return self.repo.get_connection(website_id)

    def disconnect(self, website_id: int) -> dict:
        self.repo.delete_connection(website_id)
        return {"status": "disconnected"}

    # --- sync ------------------------------------------------------------------------
    async def sync(self, website_id: int, days: int = 28) -> dict:
        conn = self.repo.get_connection(website_id)
        if conn is None:
            raise NotFoundError("ga.connection_not_found", "No GA property connected to this website")

        report = await self._call("run_daily_report", conn["property_id"], days)
        raw_path = self._archive_raw(website_id, report)
        rows = self._parse_report(report)
        imported = self.repo.upsert_daily(website_id, rows)
        return {
            "imported": imported,
            "property_id": conn["property_id"],
            "raw_path": raw_path,
            "window": {"days": days},
        }

    @staticmethod
    def _parse_report(report: dict) -> list[dict]:
        metric_index = {
            h["name"]: i for i, h in enumerate(report.get("metricHeaders", []))
        }
        missing = [name for name in METRIC_FIELDS if name not in metric_index]
        if missing:
            raise AppError("ga.unexpected_response", f"Report is missing metrics: {missing}")
        rows: list[dict] = []
        for row in report.get("rows", []):
            raw_date = row["dimensionValues"][0]["value"]  # YYYYMMDD
            date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            values = row["metricValues"]
            rows.append({
                "date": date,
                "sessions": int(float(values[metric_index["sessions"]]["value"])),
                "active_users": int(float(values[metric_index["activeUsers"]]["value"])),
                "pageviews": int(float(values[metric_index["screenPageViews"]]["value"])),
            })
        return rows

    @staticmethod
    def _archive_raw(website_id: int, payload: dict) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_dir = app_settings.data_dir / "raw" / "ga"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"website{website_id}-{stamp}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    # --- summaries (computed live — Rule 4) -------------------------------------------
    def summary(self, website_id: int, days: int = 28) -> dict:
        conn = self.repo.get_connection(website_id)
        if conn is None:
            raise NotFoundError("ga.connection_not_found", "No GA property connected to this website")

        last = self.repo.last_date(website_id)
        if not last:
            return {"connected": True, "has_data": False, "property_id": conn["property_id"]}

        end = datetime.strptime(last, "%Y-%m-%d")
        current_start = end - timedelta(days=days - 1)
        prev_end = current_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)

        current = self.repo.range_totals(website_id, current_start.isoformat(), end.isoformat())
        previous = self.repo.range_totals(website_id, prev_start.isoformat(), prev_end.isoformat())
        return {
            "connected": True,
            "has_data": True,
            "property_id": conn["property_id"],
            "property_name": conn["property_name"],
            "window": {
                "current": {"start": current_start.isoformat(), "end": end.isoformat()},
                "previous": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
            },
            "current": current,
            "previous": previous,
            "deltas": {key: current[key] - previous[key] for key in ("sessions", "active_users", "pageviews")},
            "series": self.repo.daily_series(website_id, current_start.isoformat(), end.isoformat()),
        }

    # --- helpers -------------------------------------------------------------------------
    def _require_website(self, website_id: int) -> None:
        exists = self.db.execute(
            text("SELECT 1 FROM websites WHERE id = :id"), {"id": website_id}
        ).first()
        if exists is None:
            raise NotFoundError("ga.website_not_found", f"Website {website_id} does not exist")
