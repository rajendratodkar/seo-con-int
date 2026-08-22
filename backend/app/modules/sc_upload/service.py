"""Search Console File Upload service — parses files and imports data."""
import csv
import io
import json
import logging
import re
import zipfile
from typing import Optional, Union

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
    "url_inspection": {
        "url": ["url", "page", "page url", "address"],
        "coverage": ["coverage", "status", "coverage status"],
        "crawled_as": ["crawled as", "crawler", "googlebot type"],
        "crawl_allowed": ["crawl allowed", "robots.txt", "allowed"],
        "page_fetch": ["page fetch", "fetch status", "fetch"],
        "indexing": ["indexing", "indexing status", "indexed"],
        "last_crawl": ["last crawl", "crawled date", "crawl date"],
    },
    "coverage": {
        "status": ["status", "coverage status", "type"],
        "category": ["category", "issue", "issue type", "reason"],
        "count": ["count", "number", "total", "affected urls"],
        "examples": ["examples", "sample", "urls", "example urls"],
    },
    "links": {
        "target_page": ["target page", "target url", "your page", "page"],
        "source_page": ["source page", "source url", "linking page", "from"],
        "anchor_text": ["anchor text", "anchor", "link text"],
        "first_seen": ["first seen", "first discovered", "first crawl"],
        "last_seen": ["last seen", "last discovered", "last crawl"],
    },
}

# GSC "Performance on Search" ZIP export — filename -> (dimension, column) mapping.
# These files are produced by the Search Console UI download button and contain
# one row per aggregate (date / query / page / country / device).
GSC_ZIP_PERFORMANCE = {
    "chart.csv": {"dimension": "date", "header": "Date"},
    "queries.csv": {"dimension": "query", "header": "Top queries"},
    "pages.csv": {"dimension": "page_url", "header": "Top pages"},
    "countries.csv": {"dimension": "country", "header": "Country"},
    "devices.csv": {"dimension": "device", "header": "Device"},
}
GSC_METRIC_COLUMNS = {"clicks", "impressions", "ctr", "position"}


def _clean_metric(value) -> float:
    """Parse a GSC metric cell (may be '2.63%', '36.9', '1,234')."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


class ScUploadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ScUploadRepository(self.db)

    def parse_and_import(
        self,
        website_id: int,
        filename: str,
        file_content: Union[str, bytes],
        import_type: str = "performance",
    ) -> dict:
        """Parse a file and import its data.

        Args:
            website_id: Target website ID
            filename: Original filename (used to detect format)
            file_content: Raw file content as string (CSV/JSON) or bytes (ZIP)
            import_type: Type of data (performance, url_inspection, etc.)

        Returns:
            Import summary with counts and date range.
        """
        # Validate website exists
        from sqlalchemy import text as sa_text
        website = self.db.execute(
            sa_text("SELECT id FROM websites WHERE id = :id"), {"id": website_id}
        ).mappings().first()
        if not website:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("website.not_found", f"Website {website_id} not found")

        # Create import record
        import_record = self.repo.create_import(website_id, filename, self._detect_type(filename), import_type)
        import_id = import_record["id"]

        try:
            # GSC ZIP exports are always performance reports.
            effective_type = "performance" if filename.lower().endswith(".zip") else import_type
            rows = self._parse_file(filename, file_content, import_type)

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

            # Import data based on type
            if effective_type == "performance":
                imported = self.repo.upsert_performance_rows(website_id, property_id, rows)
            elif effective_type == "url_inspection":
                imported = self.repo.upsert_url_inspection_rows(website_id, rows)
            elif effective_type == "coverage":
                imported = self.repo.upsert_coverage_rows(website_id, rows)
            elif effective_type == "links":
                imported = self.repo.upsert_links_rows(website_id, rows)
            else:
                imported = 0

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

    def _parse_file(self, filename: str, file_content: Union[str, bytes], import_type: str) -> list[dict]:
        """Route raw content to the right parser based on file extension."""
        if filename.lower().endswith(".zip"):
            content = file_content if isinstance(file_content, bytes) else file_content.encode("utf-8")
            return self._parse_gsc_zip(content)
        text = file_content.decode("utf-8", errors="replace") if isinstance(file_content, bytes) else file_content
        if self._looks_like_json(text):
            return self._parse_json(text, import_type)
        return self._parse_csv(text, import_type)

    def _parse_gsc_zip(self, content: bytes) -> list[dict]:
        """Parse a Google Search Console "Performance on Search" ZIP export.

        The export contains one CSV per dimension:
          - Chart.csv      -> per-day rows (imported with real dates)
          - Queries/Pages/Countries/Devices -> aggregates over the report
            window; these carry no date, so they are stamped with the report
            end date (from the filename, falling back to today).
        """
        report_date = self._report_end_date()
        rows: list[dict] = []
        chart_rows: list[dict] = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                names = {m.rsplit("/", 1)[-1].lower(): m for m in zf.namelist()}
                # Parse Chart.csv first so aggregated sheets can share its real
                # max date as their report end date.
                member = names.get("chart.csv")
                if member is not None:
                    with zf.open(member) as f:
                        text = f.read().decode("utf-8", errors="replace")
                    chart_rows = self._parse_gsc_sheet(text, "date", GSC_ZIP_PERFORMANCE["chart.csv"]["header"])
                if chart_rows:
                    dates = [r["date"] for r in chart_rows if r.get("date")]
                    if dates:
                        report_date = max(dates)
                rows.extend(chart_rows)
                for basename, spec in GSC_ZIP_PERFORMANCE.items():
                    if basename == "chart.csv":
                        continue
                    member = names.get(basename)
                    if member is None:
                        continue
                    with zf.open(member) as f:
                        text = f.read().decode("utf-8", errors="replace")
                    rows.extend(self._parse_gsc_sheet(text, spec["dimension"], spec["header"], report_date))
        except zipfile.BadZipFile:
            log.warning("ZIP upload was not a valid archive")
            return []
        return rows

    def _parse_gsc_sheet(
        self, content: str, dimension: str, header: str, report_date: str | None = None
    ) -> list[dict]:
        """Parse one GSC export sheet into normalized performance rows."""
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return []

        header_field = None
        for name in reader.fieldnames:
            if name.strip().lower() == header.lower():
                header_field = name
                break
        # Fallback: first non-metric column is the dimension key
        if header_field is None:
            header_field = next(
                (n for n in reader.fieldnames if n.strip().lower() not in GSC_METRIC_COLUMNS), None
            )
        if header_field is None:
            return []

        rows = []
        for row in reader:
            key = (row.get(header_field) or "").strip()
            if not key:
                continue
            metric = {}
            for col in reader.fieldnames:
                c = col.strip().lower()
                if c in GSC_METRIC_COLUMNS:
                    value = _clean_metric(row.get(col))
                    if c == "ctr" and value > 0:
                        # UI exports CTR as a percentage string; API style is a ratio.
                        metric["ctr"] = value / 100
                    else:
                        metric[c] = value
            if dimension == "date":
                rows.append({**metric, "date": key})
            else:
                rows.append({**metric, dimension: key, "date": report_date or ""})
        return rows

    def _report_end_date(self) -> str:
        from datetime import date
        return date.today().isoformat()

    def _looks_like_json(self, content: str) -> bool:
        try:
            json.loads(content)
            return True
        except (ValueError, TypeError):
            return False

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
            elif import_type == "url_inspection":
                row = self._parse_json_url_inspection_row(item)
            elif import_type == "coverage":
                row = self._parse_json_coverage_row(item)
            elif import_type == "links":
                row = self._parse_json_links_row(item)
            else:
                row = None
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

    def _parse_json_url_inspection_row(self, item: dict) -> Optional[dict]:
        """Parse a single JSON URL inspection row."""
        if "url" not in item and "pageUrl" not in item:
            return None
        return {
            "url": item.get("url") or item.get("pageUrl", ""),
            "coverage": item.get("coverage") or item.get("coverageStatus"),
            "crawled_as": item.get("crawledAs") or item.get("crawlerType"),
            "crawl_allowed": item.get("crawlAllowed") or item.get("robotsTxt"),
            "page_fetch": item.get("pageFetch") or item.get("fetchStatus"),
            "indexing": item.get("indexing") or item.get("indexingStatus"),
            "last_crawl": item.get("lastCrawl") or item.get("crawlDate"),
        }

    def _parse_json_coverage_row(self, item: dict) -> Optional[dict]:
        """Parse a single JSON coverage row."""
        status = item.get("status") or item.get("coverageStatus")
        category = item.get("category") or item.get("issue")
        if not status:
            return None
        return {
            "status": status,
            "category": category or "Unknown",
            "count": int(item.get("count", 0)),
            "examples": json.dumps(item.get("examples", [])) if item.get("examples") else None,
        }

    def _parse_json_links_row(self, item: dict) -> Optional[dict]:
        """Parse a single JSON links row."""
        target = item.get("targetPage") or item.get("target")
        source = item.get("sourcePage") or item.get("source")
        if not target or not source:
            return None
        return {
            "target_page": target,
            "source_page": source,
            "anchor_text": item.get("anchorText") or item.get("anchor"),
            "first_seen": item.get("firstSeen") or item.get("firstDiscovered"),
            "last_seen": item.get("lastSeen") or item.get("lastDiscovered"),
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

        # Validate based on import type
        if not any(normalized.values()):
            return None

        return normalized

    def _detect_type(self, filename: str) -> str:
        """Detect file type from filename extension."""
        lower = filename.lower()
        if lower.endswith(".json"):
            return "json"
        if lower.endswith(".zip"):
            return "zip"
        return "csv"

    def _extract_site_url(self, rows: list[dict]) -> str:
        """Extract site URL from page URLs in the data."""
        from urllib.parse import urlparse
        for row in rows:
            # Check multiple URL fields depending on import type
            page_url = row.get("page_url") or row.get("url") or row.get("target_page") or ""
            if page_url:
                try:
                    parsed = urlparse(page_url)
                    if parsed.netloc:
                        return f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    continue
        return "https://unknown.com"
