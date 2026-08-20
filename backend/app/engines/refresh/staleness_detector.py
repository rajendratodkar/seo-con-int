"""Staleness detector — identifies pages that need refreshing.

Flags pages based on age, declining metrics, and outdated metadata.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def detect_stale_pages(
    db: Session,
    website_id: int,
    min_age_days: int = 90,
    lookback_days: int = 28,
) -> list[dict]:
    """Find pages that are stale based on multiple signals.

    Returns a list of pages with staleness scores and reasons.
    """
    # Get all pages for the website
    pages = db.execute(
        text(
            "SELECT id, url, title, created_at, updated_at "
            "FROM pages WHERE website_id = :w "
            "ORDER BY updated_at ASC"
        ),
        {"w": website_id},
    ).mappings().all()

    if not pages:
        return []

    stale_pages = []

    for page in pages:
        signals = []
        staleness_score = 0.0

        # Signal 1: Page age (days since last update)
        page_dict = dict(page)
        age_days = _days_since(page_dict.get("updated_at") or page_dict.get("created_at"))
        if age_days >= min_age_days:
            age_score = min(age_days / (min_age_days * 3), 1.0)  # caps at 3x threshold
            staleness_score += age_score * 0.3
            signals.append({
                "type": "age",
                "value": age_days,
                "threshold": min_age_days,
                "message": f"Page is {age_days} days old (threshold: {min_age_days})",
            })

        # Signal 2: Declining impressions
        imp_trend = _get_impression_trend(db, page_dict["id"], lookback_days)
        if imp_trend["declining"]:
            decline_pct = imp_trend["decline_pct"]
            trend_score = min(decline_pct / 50, 1.0)  # caps at 50% decline
            staleness_score += trend_score * 0.4
            signals.append({
                "type": "impression_decline",
                "value": decline_pct,
                "message": f"Impressions dropped {decline_pct:.1f}% over {lookback_days} days",
            })

        # Signal 3: Declining clicks
        click_trend = _get_click_trend(db, page_dict["id"], lookback_days)
        if click_trend["declining"]:
            decline_pct = click_trend["decline_pct"]
            trend_score = min(decline_pct / 50, 1.0)
            staleness_score += trend_score * 0.2
            signals.append({
                "type": "click_decline",
                "value": decline_pct,
                "message": f"Clicks dropped {decline_pct:.1f}% over {lookback_days} days",
            })

        # Signal 4: Low or declining CTR
        ctr_data = _get_ctr_trend(db, page_dict["id"], lookback_days)
        if ctr_data["declining"]:
            staleness_score += 0.1
            signals.append({
                "type": "ctr_decline",
                "value": ctr_data["decline_pct"],
                "message": f"CTR dropped {ctr_data['decline_pct']:.1f}% — title/description may be stale",
            })

        if signals:
            # Normalize score to 0-1
            staleness_score = min(staleness_score, 1.0)
            stale_pages.append({
                "page_id": page_dict["id"],
                "url": page_dict["url"],
                "title": page_dict.get("title"),
                "age_days": age_days,
                "staleness_score": round(staleness_score, 3),
                "signals": signals,
            })

    # Sort by staleness score descending
    stale_pages.sort(key=lambda p: p["staleness_score"], reverse=True)
    return stale_pages


def _get_impression_trend(db: Session, page_id: int, days: int) -> dict:
    """Compare first-half vs second-half impressions for a page."""
    half = days // 2
    row = db.execute(
        text(
            "SELECT "
            "SUM(CASE WHEN date >= date('now', :start1) AND date < date('now', :end1) THEN impressions ELSE 0 END) AS first_half, "
            "SUM(CASE WHEN date >= date('now', :start2) THEN impressions ELSE 0 END) AS second_half "
            "FROM search_console_data WHERE page_id = :pid"
        ),
        {"pid": page_id, "start1": f"-{days} days", "end1": f"-{half} days", "start2": f"-{half} days"},
    ).mappings().first()

    if not row:
        return {"declining": False, "decline_pct": 0}

    first = row["first_half"] or 0
    second = row["second_half"] or 0

    if first == 0:
        return {"declining": False, "decline_pct": 0}

    change_pct = ((second - first) / first) * 100
    return {"declining": change_pct < -5, "decline_pct": abs(change_pct)}


def _get_click_trend(db: Session, page_id: int, days: int) -> dict:
    """Compare first-half vs second-half clicks for a page."""
    half = days // 2
    row = db.execute(
        text(
            "SELECT "
            "SUM(CASE WHEN date >= date('now', :start1) AND date < date('now', :end1) THEN clicks ELSE 0 END) AS first_half, "
            "SUM(CASE WHEN date >= date('now', :start2) THEN clicks ELSE 0 END) AS second_half "
            "FROM search_console_data WHERE page_id = :pid"
        ),
        {"pid": page_id, "start1": f"-{days} days", "end1": f"-{half} days", "start2": f"-{half} days"},
    ).mappings().first()

    if not row:
        return {"declining": False, "decline_pct": 0}

    first = row["first_half"] or 0
    second = row["second_half"] or 0

    if first == 0:
        return {"declining": False, "decline_pct": 0}

    change_pct = ((second - first) / first) * 100
    return {"declining": change_pct < -5, "decline_pct": abs(change_pct)}


def _get_ctr_trend(db: Session, page_id: int, days: int) -> dict:
    """Compare first-half vs second-half CTR for a page."""
    half = days // 2
    row = db.execute(
        text(
            "SELECT "
            "CASE WHEN SUM(CASE WHEN date >= date('now', :start1) AND date < date('now', :end1) THEN impressions ELSE 0 END) > 0 "
            "THEN CAST(SUM(CASE WHEN date >= date('now', :start1) AND date < date('now', :end1) THEN clicks ELSE 0 END) AS REAL) "
            "/ SUM(CASE WHEN date >= date('now', :start1) AND date < date('now', :end1) THEN impressions ELSE 0 END) "
            "ELSE 0 END AS first_ctr, "
            "CASE WHEN SUM(CASE WHEN date >= date('now', :start2) THEN impressions ELSE 0 END) > 0 "
            "THEN CAST(SUM(CASE WHEN date >= date('now', :start2) THEN clicks ELSE 0 END) AS REAL) "
            "/ SUM(CASE WHEN date >= date('now', :start2) THEN impressions ELSE 0 END) "
            "ELSE 0 END AS second_ctr "
            "FROM search_console_data WHERE page_id = :pid"
        ),
        {"pid": page_id, "start1": f"-{days} days", "end1": f"-{half} days", "start2": f"-{half} days"},
    ).mappings().first()

    if not row:
        return {"declining": False, "decline_pct": 0}

    first = row["first_ctr"] or 0
    second = row["second_ctr"] or 0

    if first == 0:
        return {"declining": False, "decline_pct": 0}

    change_pct = ((second - first) / first) * 100
    return {"declining": change_pct < -10, "decline_pct": abs(change_pct)}


def _days_since(date_str: str | None) -> int:
    """Calculate days since a date string."""
    if not date_str:
        return 999  # very old if no date
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now() - dt.replace(tzinfo=None)).days
    except (ValueError, TypeError):
        return 999
