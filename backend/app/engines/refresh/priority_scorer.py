"""Priority scorer — computes a unified refresh priority score.

Combines staleness, traffic trends, and SEO findings into a single
0-100 priority score with suggested changes and priority dates.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def score_priority(
    stale_pages: list[dict],
    trends: list[dict],
    db: Session,
    website_id: int,
    weights: dict | None = None,
) -> list[dict]:
    """Score and rank pages for refresh priority.

    Args:
        stale_pages: Output from staleness_detector.detect_stale_pages()
        trends: Output from trend_analyzer.analyze_trends()
        db: Database session
        website_id: Website ID
        weights: Optional custom weights {staleness, traffic, findings}

    Returns:
        List of pages with priority scores, suggested changes, and priority dates.
    """
    w = weights or {"staleness": 0.35, "traffic": 0.40, "findings": 0.25}

    # Index trends by page_id
    trend_map = {t["page_id"]: t for t in trends}

    # Get SEO findings per page
    findings_map = _get_findings_per_page(db, website_id)

    # Get current metrics per page
    metrics_map = _get_current_metrics(db, website_id)

    scored = []
    for sp in stale_pages:
        pid = sp["page_id"]

        # Staleness component (0-1)
        staleness = sp.get("staleness_score", 0)

        # Traffic component (0-1) — from trend data
        trend = trend_map.get(pid, {})
        avg_change = trend.get("avg_impression_change", 0)
        # Map: -50% change → 1.0, 0% → 0.3, +50% → 0.0
        traffic = max(0, min(1, 0.3 - (avg_change / 100)))

        # Findings component (0-1) — based on open SEO issues
        findings = findings_map.get(pid, 0)
        findings_score = min(findings / 10, 1.0)  # caps at 10 findings

        # Weighted priority score (0-100)
        priority = (staleness * w["staleness"] + traffic * w["traffic"] + findings_score * w["findings"]) * 100
        priority = min(round(priority, 1), 100)

        # Generate suggested changes
        suggested = _suggest_changes(sp, trend, findings_map.get(pid, 0))

        # Calculate priority date (higher score = sooner)
        priority_date = _calculate_priority_date(priority)

        # Current metrics
        metrics = metrics_map.get(pid, {})

        scored.append({
            "page_id": pid,
            "url": sp["url"],
            "title": sp.get("title"),
            "priority_score": priority,
            "priority_date": priority_date,
            "staleness_score": staleness,
            "traffic_trend": trend.get("overall_trend", "unknown"),
            "avg_impression_change": trend.get("avg_impression_change", 0),
            "open_findings": findings_map.get(pid, 0),
            "current_clicks": metrics.get("clicks", 0),
            "current_impressions": metrics.get("impressions", 0),
            "current_position": metrics.get("position", 0),
            "suggested_changes": suggested,
            "signals": sp.get("signals", []),
        })

    # Sort by priority score descending
    scored.sort(key=lambda p: p["priority_score"], reverse=True)
    return scored


def _get_findings_per_page(db: Session, website_id: int) -> dict[int, int]:
    """Get count of open SEO findings per page."""
    rows = db.execute(
        text(
            "SELECT page_id, COUNT(*) AS count "
            "FROM seo_findings WHERE website_id = :w AND status = 'open' AND page_id IS NOT NULL "
            "GROUP BY page_id"
        ),
        {"w": website_id},
    ).mappings().all()
    return {r["page_id"]: r["count"] for r in rows}


def _get_current_metrics(db: Session, website_id: int) -> dict[int, dict]:
    """Get current SC metrics per page (last 28 days)."""
    rows = db.execute(
        text(
            "SELECT page_id, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
            "CASE WHEN SUM(impressions) > 0 THEN ROUND(SUM(position * impressions) / SUM(impressions), 1) ELSE 0 END AS position "
            "FROM search_console_data WHERE website_id = :w "
            "AND page_id IS NOT NULL AND date >= date('now', '-28 days') "
            "GROUP BY page_id"
        ),
        {"w": website_id},
    ).mappings().all()
    return {r["page_id"]: dict(r) for r in rows}


def _suggest_changes(stale_page: dict, trend: dict | None, findings_count: int) -> list[dict]:
    """Generate specific change suggestions based on signals."""
    changes = []

    for signal in stale_page.get("signals", []):
        if signal["type"] == "age":
            changes.append({
                "type": "content",
                "priority": "high",
                "description": "Update content with fresh information, statistics, and examples",
                "reason": signal["message"],
            })
        elif signal["type"] == "impression_decline":
            changes.append({
                "type": "keywords",
                "priority": "high",
                "description": "Research new keywords and update headings/meta to match current search intent",
                "reason": signal["message"],
            })
        elif signal["type"] == "click_decline":
            changes.append({
                "type": "title_meta",
                "priority": "high",
                "description": "Rewrite title and meta description to improve CTR",
                "reason": signal["message"],
            })
        elif signal["type"] == "ctr_decline":
            changes.append({
                "type": "title_meta",
                "priority": "medium",
                "description": "Optimize title tag and meta description for better click-through",
                "reason": signal["message"],
            })

    # Add structural suggestions based on findings
    if findings_count > 0:
        changes.append({
            "type": "seo_fixes",
            "priority": "medium",
            "description": f"Address {findings_count} open SEO findings for this page",
            "reason": f"{findings_count} open issues in SEO analysis",
        })

    # Always suggest checking links
    if stale_page.get("age_days", 0) > 180:
        changes.append({
            "type": "links",
            "priority": "low",
            "description": "Check for broken internal/external links and update outdated references",
            "reason": f"Page is {stale_page['age_days']} days old — links may have gone stale",
        })

    return changes


def _calculate_priority_date(priority_score: float) -> str:
    """Calculate when the page should be refreshed based on priority.

    Higher score = sooner deadline.
    """
    from datetime import datetime, timedelta

    now = datetime.now()

    if priority_score >= 80:
        days = 7    # Within a week
    elif priority_score >= 60:
        days = 14   # Within 2 weeks
    elif priority_score >= 40:
        days = 30   # Within a month
    elif priority_score >= 20:
        days = 60   # Within 2 months
    else:
        days = 90   # Within 3 months

    return (now + timedelta(days=days)).strftime("%Y-%m-%d")
