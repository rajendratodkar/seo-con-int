"""raw -> normalized pipeline (Rule 7: raw payloads are never overwritten)."""
from datetime import datetime, timezone

SC_DIMENSIONS = ["date", "query", "page"]


def normalize_api_rows(rows: list[dict]) -> list[dict]:
    """Convert Search Console API rows to normalized records."""
    normalized = []
    for row in rows:
        keys = dict(zip(SC_DIMENSIONS, row.get("keys", [])))
        normalized.append({
            "date": keys.get("date"),
            "query": keys.get("query"),
            "page_url": keys.get("page"),
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return normalized


def normalize_manual_rows(rows: list[dict]) -> list[dict]:
    """Validate/normalize rows supplied through the manual import endpoint."""
    normalized = []
    for row in rows:
        normalized.append({
            "date": row["date"],
            "query": row.get("query"),
            "page_url": row.get("page_url"),
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return normalized


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
