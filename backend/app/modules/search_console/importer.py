"""Historical and incremental imports (raw first, then normalized — Rule 7)."""
import logging
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.search_console.api_client import SearchConsoleClient
from app.modules.search_console.normalizer import SC_DIMENSIONS, normalize_api_rows
from app.modules.search_console.repository import SearchConsoleRepository

log = logging.getLogger(__name__)

HISTORICAL_DAYS = 90
INCREMENTAL_DAYS = 7


class SearchConsoleImporter:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SearchConsoleRepository(db)

    async def import_range(
        self,
        property_id: int,
        website_id: int,
        access_token: str,
        start_date: str,
        end_date: str,
        sync_type: str,
    ) -> int:
        prop = self.repo.get_property(property_id)
        client = SearchConsoleClient(access_token)
        sync_log_id = self._start_log(property_id, sync_type)

        imported = 0
        start_row = 0
        try:
            while True:
                report = await client.query_report(
                    prop["site_url"], start_date, end_date, SC_DIMENSIONS, start_row=start_row
                )
                rows = report.get("rows", [])
                if rows:
                    # Rule 7: persist untouched payload before normalizing
                    self.repo.store_raw(
                        property_id, sync_log_id,
                        {"startDate": start_date, "endDate": end_date, "dimensions": SC_DIMENSIONS, "startRow": start_row},
                        report,
                    )
                    imported += self.repo.upsert_rows(website_id, property_id, normalize_api_rows(rows))
                    self.db.commit()
                if len(rows) < 25000:
                    break
                start_row += 25000
            self._finish_log(sync_log_id, "completed", imported)
        except Exception as exc:
            self._finish_log(sync_log_id, "failed", imported, str(exc))
            raise
        return imported

    def historical_window(self) -> tuple[str, str]:
        end = date.today() - timedelta(days=2)  # GSC data lags ~2 days
        start = end - timedelta(days=HISTORICAL_DAYS)
        return start.isoformat(), end.isoformat()

    def incremental_window(self) -> tuple[str, str]:
        end = date.today() - timedelta(days=2)
        start = end - timedelta(days=INCREMENTAL_DAYS)
        return start.isoformat(), end.isoformat()

    def _start_log(self, property_id: int, sync_type: str) -> int:
        result = self.db.execute(
            text(
                "INSERT INTO sync_logs (module, entity_id, sync_type, status) "
                "VALUES ('search_console', :entity_id, :sync_type, 'running')"
            ),
            {"entity_id": property_id, "sync_type": sync_type},
        )
        self.db.commit()
        return result.lastrowid

    def _finish_log(self, log_id: int, status: str, records: int, error: str | None = None) -> None:
        self.db.execute(
            text(
                "UPDATE sync_logs SET status=:status, finished_at=datetime('now'), "
                "records_imported=:records, error_message=:error WHERE id=:id"
            ),
            {"status": status, "records": records, "error": error, "id": log_id},
        )
        self.db.commit()
