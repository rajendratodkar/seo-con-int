"""Trend analyzer — computes multi-period trends per page.

Classifies pages as declining, stable, or growing based on
30/60/90-day windows.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def analyze_trends(db: Session, website_id: int, page_ids: list[int] | None = None) -> list[dict]:
    """Compute trend data for pages.

    Returns trend classification for each page with multi-period data.
    """
    if not page_ids:
        # Get all pages for the website
        rows = db.execute(
            text("SELECT id FROM pages WHERE website_id = :w"),
            {"w": website_id},
        ).mappings().all()
        page_ids = [r["id"] for r in rows]

    if not page_ids:
        return []

    trends = []
    for pid in page_ids:
        trend = _analyze_page_trend(db, pid)
        if trend:
            trends.append(trend)

    # Sort by overall trend (declining first)
    trend_order = {"declining": 0, "stable": 1, "growing": 2}
    trends.sort(key=lambda t: trend_order.get(t["overall_trend"], 1))
    return trends


def _analyze_page_trend(db: Session, page_id: int) -> dict | None:
    """Analyze trend for a single page across 30/60/90-day windows."""
    windows = [30, 60, 90]
    window_data = {}

    for days in windows:
        half = days // 2
        row = db.execute(
            text(
                "SELECT "
                "SUM(CASE WHEN date >= date('now', :s1) AND date < date('now', :e1) THEN impressions ELSE 0 END) AS imp_first, "
                "SUM(CASE WHEN date >= date('now', :s2) THEN impressions ELSE 0 END) AS imp_second, "
                "SUM(CASE WHEN date >= date('now', :s1) AND date < date('now', :e1) THEN clicks ELSE 0 END) AS clk_first, "
                "SUM(CASE WHEN date >= date('now', :s2) THEN clicks ELSE 0 END) AS clk_second, "
                "COUNT(DISTINCT query) AS unique_queries "
                "FROM search_console_data WHERE page_id = :pid"
            ),
            {"pid": page_id, "s1": f"-{days} days", "e1": f"-{half} days", "s2": f"-{half} days"},
        ).mappings().first()

        if not row:
            continue

        imp_first = row["imp_first"] or 0
        imp_second = row["imp_second"] or 0
        clk_first = row["clk_first"] or 0
        clk_second = row["clk_second"] or 0

        imp_change = _pct_change(imp_first, imp_second)
        clk_change = _pct_change(clk_first, clk_second)

        window_data[days] = {
            "impressions_first": imp_first,
            "impressions_second": imp_second,
            "impressions_change_pct": imp_change,
            "clicks_first": clk_first,
            "clicks_second": clk_second,
            "clicks_change_pct": clk_change,
            "unique_queries": row["unique_queries"] or 0,
        }

    if not window_data:
        return None

    # Classify overall trend
    # Use 30-day trend as primary signal, 60/90 as confirmation
    imp_30 = window_data.get(30, {}).get("impressions_change_pct", 0)
    clk_30 = window_data.get(30, {}).get("clicks_change_pct", 0)
    imp_60 = window_data.get(60, {}).get("impressions_change_pct", 0)
    imp_90 = window_data.get(90, {}).get("impressions_change_pct", 0)

    # Overall impression trend (weighted average)
    avg_change = (imp_30 * 0.5 + imp_60 * 0.3 + imp_90 * 0.2) if len(window_data) > 1 else imp_30

    if avg_change < -10:
        overall = "declining"
    elif avg_change > 10:
        overall = "growing"
    else:
        overall = "stable"

    return {
        "page_id": page_id,
        "overall_trend": overall,
        "avg_impression_change": round(avg_change, 1),
        "windows": window_data,
    }


def _pct_change(old: int, new: int) -> float:
    """Calculate percentage change."""
    if old == 0:
        return 100.0 if new > 0 else 0.0
    return round(((new - old) / old) * 100, 1)
