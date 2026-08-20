"""Search Console File Upload service — parses files and imports data."""
import csv
import io
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.sc_upload.repository import ScUploadRepository

log = logging.getLogger(__name__)

# Column name mappings (case-insensitive)
COLUMN_MAPS = {
    "performance": {
        "date": ["date", "dates", "day"],
        "query": ["query", "queries", "keyword", "search query", "search term"],
        "page_url": ["page", "url", "page url", "landing page", "page_url"],
        "clicks": ["clicks", "click"],
        "impressions": ["impressions", "impression"],
        "ctr": ["ctr", "click-through rate", "click through rate"],
        "position": ["position", "avg. position", "average position", "avg position"],
    },
}


class ScUploadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ScUploadRepository(self.db)

    def parse_and_import(
        self,
        website_id: int,
        filename: str,
        file_content: str,
        import_type: str = "performance",
    ) -> dict:
        """Parse a file and import its data.

        Args:
            website_id: Target website ID
            filename: Original filename (used to detect format)
            file_content: Raw file content as string
            import_type: Type of data (performance, url_inspection, etc.)

        Returns:
            Import summary with counts and date range.
        """
        # Create import record
        import_record = self.repo.create_import(website_id, filename, self._detect_type(filename), import_type)
        import_id = import_record["id"]

        try:
            # Parse file based on type
            if import_record["file_type"] == "json":
                rows = self._parse_json(file_content, import_type)
            else:
                rows = self._parse_csv(file_content, import_type)

            if not rows:
                self.repo.update_import(
                    import_id,
                    status="completed",
                    rows_total=0,
                    rows_imported=0,
                    rows_skipped=0,
                    completed_at="datetime('now')",
                )
                return {
                    "import_id": import_id,
                    "rows_imported": 0,
                    "rows_skipped": 0,
                    "rows_errors": 0,
                    "error_count": 0,
                    "message": "No valid rows found in file",
                }

            # Get or create property for this website
            site_url = self._extract_site_url(rows)
            property_id = self.repo.get_or_create_property(website_id, site_url)

            # Import data
            if import_type == "performance":
                imported = self.repo.upsert_performance_rows(website_id, property_id, rows)
            else:
                imported = 0  # Other import types TBD

            # Calculate date range
            dates = [r.get("date") for r in rows if r.get("date")]
            date_range_start = min(dates) if dates else None
            date_range_end = max(dates) if dates else None

            # Update import record
            self.repo.update_import(
                import_id,
                status="completed",
                rows_total=len(rows),
                rows_imported=imported,
                rows_skipped=len(rows) - imported,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                completed_at="datetime('now')",
            )

            return {
                "import_id": import_id,
                "rows_imported": imported,
                "rows_skipped": len(rows) - imported,
                "rows_errors": 0,
                "error_count": 0,
                "date_range_start": date_range_start,
                "date_range_end": date_range_end,
                "message": f"Successfully imported {imported} rows from {filename}",
            }

        except Exception as e:
            log.exception("Import failed")
            self.repo.update_import(
                import_id,
                status="failed",
                error_details=json.dumps([{"error": str(e)}]),
            )
            return {
                "import_id": import_id,
                "rows_imported": 0,
                "rows_skipped": 0,
                "rows_errors": 0,
                "error_count": 1,
                "message": f"Import failed: {str(e)}",
            }

    def _parse_csv(self, content: str, import_type: str) -> list[dict]:
        """Parse CSV content and normalize column names."""
        reader = csv.DictReader(io.StringIO(content))
        rows = []
        column_map = COLUMN_MAPS.get(import_type, COLUMN_MAPS["performance"])

        for i, row in enumerate(reader):
            try:
                normalized = self._normalize_row(row, column_map)
                if normalized:
                    rows.append(normalized)
            except Exception as e:
                log.warning(f"Skipping row {i+1}: {e}")
                continue

        return rows

    def _parse_json(self, content: str, import_type: str) -> list[dict]:
        """Parse JSON content (GSC API response format)."""
        data = json.loads(content)

        # Handle both direct array and { "rows": [...] } formats
        if isinstance(data, list):
            rows_data = data
        elif isinstance(data, dict) and "rows" in data:
            rows_data = data["rows"]
        else:
            return []

        rows = []
        for item in rows_data:
            if import_type == "performance":
                row = self._parse_json_performance_row(item)
                if row:
                    rows.append(row)

        return rows

    def _parse_json_performance_row(self, item: dict) -> Optional[dict]:
        """Parse a single JSON performance row (GSC API format)."""
        keys = item.get("keys", [])
        if len(keys) < 2:
            return None

        return {
            "query": keys[0],
            "page_url": keys[1],
            "clicks": item.get("clicks", 0),
            "impressions": item.get("impressions", 0),
            "ctr": item.get("ctr", 0.0),
            "position": item.get("position", 0.0),
            "date": item.get("date", ""),
        }

    def _normalize_row(self, row: dict, column_map: dict) -> Optional[dict]:
        """Normalize a CSV row using column name mappings."""
        normalized = {}

        for target_field, possible_names in column_map.items():
            for name in possible_names:
                # Case-insensitive search
                for key in row:
                    if key.lower().strip() == name.lower():
                        value = row[key]
                        # Clean up value
                        if value:
                            value = value.strip()
                            # Convert numeric fields
                            if target_field in ("clicks", "impressions"):
                                value = int(float(value)) if value else 0
                            elif target_field in ("ctr", "position"):
                                # Handle percentage format (e.g., "2.63%")
                                if isinstance(value, str) and "%" in value:
                                    value = float(value.replace("%", "")) / 100
                                else:
                                    value = float(value) if value else 0.0
                        normalized[target_field] = value
                        break
                if target_field in normalized:
                    break

        # Must have at least one metric
        has_metrics = any(normalized.get(f) for f in ("clicks", "impressions", "ctr", "position"))
        if not has_metrics:
            return None

        return normalized

    def _detect_type(self, filename: str) -> str:
        """Detect file type from filename extension."""
        if filename.lower().endswith(".json"):
            return "json"
        return "csv"

    def _extract_site_url(self, rows: list[dict]) -> str:
        """Extract site URL from page URLs in the data."""
        for row in rows:
            page_url = row.get("page_url", "")
            if page_url:
                # Extract base URL (e.g., "https://example.com" from "https://example.com/page")
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    return f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    continue
        return "https://unknown.com"
