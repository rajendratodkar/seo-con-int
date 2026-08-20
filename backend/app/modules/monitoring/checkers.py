"""Monitoring checkers — each detects a specific type of issue.

Every checker returns a list of dicts:
    {severity, title, message, data}
or an empty list if nothing was found.
"""
import json
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Ranking Drop Checker
# ---------------------------------------------------------------------------

def check_ranking_drop(db: Session, website_id: int, config: dict) -> list[dict]:
    """Detect queries whose average position worsened beyond the threshold."""
    threshold_pct = config.get("threshold_pct", 15)  # % worsening
    min_impressions = config.get("min_impressions", 50)
    lookback = config.get("lookback_days", 7)

    current_start = _days_ago(lookback)
    previous_start = _days_ago(lookback * 2)
    previous_end = _days_ago(lookback)

    # Current period avg position per query
    current = {
        r.query: r.avg_pos
        for r in db.execute(
            text(
                "SELECT query, AVG(position) AS avg_pos, SUM(impressions) AS imp "
                "FROM search_console_data "
                "WHERE website_id = :wid AND date >= :start AND query IS NOT NULL "
                "GROUP BY query HAVING imp >= :min_imp"
            ),
            {"wid": website_id, "start": current_start, "min_imp": min_impressions},
        ).mappings().all()
    }

    # Previous period avg position per query
    previous = {
        r.query: r.avg_pos
        for r in db.execute(
            text(
                "SELECT query, AVG(position) AS avg_pos "
                "FROM search_console_data "
                "WHERE website_id = :wid AND date >= :pstart AND date < :pend AND query IS NOT NULL "
                "GROUP BY query"
            ),
            {"wid": website_id, "pstart": previous_start, "pend": previous_end},
        ).mappings().all()
    }

    alerts = []
    for query, cur_pos in current.items():
        prev_pos = previous.get(query)
        if prev_pos is None or prev_pos == 0:
            continue
        worsened_pct = ((cur_pos - prev_pos) / prev_pos) * 100
        if worsened_pct >= threshold_pct:
            alerts.append({
                "severity": "critical" if cur_pos > 20 else "warning",
                "title": f"Ranking drop: \"{query}\"",
                "message": (
                    f"Average position worsened {worsened_pct:.0f}% "
                    f"(from {prev_pos:.1f} → {cur_pos:.1f}) over the last {lookback} days."
                ),
                "data": {
                    "query": query,
                    "previous_position": round(prev_pos, 1),
                    "current_position": round(cur_pos, 1),
                    "worsened_pct": round(worsened_pct, 1),
                },
            })
    return alerts


# ---------------------------------------------------------------------------
# Traffic Drop Checker
# ---------------------------------------------------------------------------

def check_traffic_drop(db: Session, website_id: int, config: dict) -> list[dict]:
    """Detect significant drops in total clicks compared to the previous period."""
    threshold_pct = config.get("threshold_pct", 20)
    lookback = config.get("lookback_days", 7)

    current_start = _days_ago(lookback)
    previous_start = _days_ago(lookback * 2)
    previous_end = _days_ago(lookback)

    current_clicks = db.execute(
        text(
            "SELECT COALESCE(SUM(clicks), 0) AS total "
            "FROM search_console_data WHERE website_id = :wid AND date >= :start"
        ),
        {"wid": website_id, "start": current_start},
    ).scalar()

    previous_clicks = db.execute(
        text(
            "SELECT COALESCE(SUM(clicks), 0) AS total "
            "FROM search_console_data WHERE website_id = :wid AND date >= :pstart AND date < :pend"
        ),
        {"wid": website_id, "pstart": previous_start, "pend": previous_end},
    ).scalar()

    if previous_clicks == 0:
        return []

    drop_pct = ((previous_clicks - current_clicks) / previous_clicks) * 100
    if drop_pct >= threshold_pct:
        return [{
            "severity": "critical" if drop_pct >= 40 else "warning",
            "title": "Traffic drop detected",
            "message": (
                f"Clicks dropped {drop_pct:.0f}% "
                f"(from {previous_clicks:,} → {current_clicks:,}) over the last {lookback} days."
            ),
            "data": {
                "previous_clicks": previous_clicks,
                "current_clicks": current_clicks,
                "drop_pct": round(drop_pct, 1),
                "lookback_days": lookback,
            },
        }]
    return []


# ---------------------------------------------------------------------------
# CTR Drop Checker
# ---------------------------------------------------------------------------

def check_ctr_drop(db: Session, website_id: int, config: dict) -> list[dict]:
    """Detect queries where CTR dropped significantly despite stable/improving position."""
    threshold_pct = config.get("threshold_pct", 20)
    min_impressions = config.get("min_impressions", 100)
    lookback = config.get("lookback_days", 7)

    current_start = _days_ago(lookback)
    previous_start = _days_ago(lookback * 2)
    previous_end = _days_ago(lookback)

    current = {
        r.query: {"ctr": r.avg_ctr, "pos": r.avg_pos, "imp": r.imp}
        for r in db.execute(
            text(
                "SELECT query, AVG(ctr) AS avg_ctr, AVG(position) AS avg_pos, SUM(impressions) AS imp "
                "FROM search_console_data "
                "WHERE website_id = :wid AND date >= :start AND query IS NOT NULL "
                "GROUP BY query HAVING imp >= :min_imp"
            ),
            {"wid": website_id, "start": current_start, "min_imp": min_impressions},
        ).mappings().all()
    }

    previous = {
        r.query: {"ctr": r.avg_ctr, "pos": r.avg_pos}
        for r in db.execute(
            text(
                "SELECT query, AVG(ctr) AS avg_ctr, AVG(position) AS avg_pos "
                "FROM search_console_data "
                "WHERE website_id = :wid AND date >= :pstart AND date < :pend AND query IS NOT NULL "
                "GROUP BY query"
            ),
            {"wid": website_id, "pstart": previous_start, "pend": previous_end},
        ).mappings().all()
    }

    alerts = []
    for query, cur in current.items():
        prev = previous.get(query)
        if not prev or prev["ctr"] == 0:
            continue
        ctr_drop_pct = ((prev["ctr"] - cur["ctr"]) / prev["ctr"]) * 100
        # Only alert if position stayed roughly the same (within 2 spots)
        pos_stable = abs(cur["pos"] - prev["pos"]) <= 2
        if ctr_drop_pct >= threshold_pct and pos_stable:
            alerts.append({
                "severity": "warning",
                "title": f"CTR drop: \"{query}\"",
                "message": (
                    f"CTR dropped {ctr_drop_pct:.0f}% "
                    f"(from {prev['ctr']*100:.1f}% → {cur['ctr']*100:.1f}%) "
                    f"while position stayed stable (~{cur['pos']:.1f})."
                ),
                "data": {
                    "query": query,
                    "previous_ctr": round(prev["ctr"] * 100, 2),
                    "current_ctr": round(cur["ctr"] * 100, 2),
                    "position": round(cur["pos"], 1),
                },
            })
    return alerts


# ---------------------------------------------------------------------------
# New SEO Issues Checker
# ---------------------------------------------------------------------------

def check_new_seo_issues(db: Session, website_id: int, config: dict) -> list[dict]:
    """Detect newly created open SEO findings."""
    min_severity = config.get("min_severity", "warning")  # warning | critical
    lookback_days = config.get("lookback_days", 1)
    since = _days_ago(lookback_days)

    severity_order = {"info": 0, "warning": 1, "critical": 2}
    min_sev = severity_order.get(min_severity, 1)

    rows = db.execute(
        text(
            "SELECT id, recommendation, severity, evidence "
            "FROM seo_findings "
            "WHERE website_id = :wid AND status = 'open' AND created_at >= :since"
        ),
        {"wid": website_id, "since": since},
    ).mappings().all()

    alerts = []
    for row in rows:
        if severity_order.get(row.severity, 0) < min_sev:
            continue
        alerts.append({
            "severity": row.severity,
            "title": f"New SEO issue: {row.recommendation[:80]}",
            "message": f"{row.evidence}",
            "data": {"finding_id": row.id, "severity": row.severity},
        })
    return alerts


# ---------------------------------------------------------------------------
# Crawl Error Checker
# ---------------------------------------------------------------------------

def check_crawl_errors(db: Session, website_id: int, config: dict) -> list[dict]:
    """Detect pages with HTTP errors or crawl failures."""
    min_status = config.get("min_status_code", 400)
    lookback_days = config.get("lookback_days", 7)
    since = _days_ago(lookback_days)

    rows = db.execute(
        text(
            "SELECT id, url, title, status_code "
            "FROM pages "
            "WHERE website_id = :wid AND ("
            "(status_code IS NOT NULL AND status_code >= :min_status) "
            "OR (crawl_status = 'failed' AND last_crawled_at >= :since))"
        ),
        {"wid": website_id, "min_status": min_status, "since": since},
    ).mappings().all()

    alerts = []
    for row in rows:
        if row.status_code and row.status_code >= 500:
            severity = "critical"
        elif row.status_code and row.status_code >= 400:
            severity = "warning"
        else:
            severity = "warning"

        title = row.title or row.url
        alerts.append({
            "severity": severity,
            "title": f"Crawl error: {title[:60]}",
            "message": (
                f"HTTP {row.status_code}" if row.status_code
                else "Crawl failed"
            ) + f" — {row.url}",
            "data": {"page_id": row.id, "url": row.url, "status_code": row.status_code},
        })
    return alerts


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

CHECKERS = {
    "ranking_drop": check_ranking_drop,
    "traffic_drop": check_traffic_drop,
    "ctr_drop": check_ctr_drop,
    "new_seo_issue": check_new_seo_issues,
    "crawl_error": check_crawl_errors,
}


def run_checker(rule_type: str, db: Session, website_id: int, config: dict) -> list[dict]:
    checker = CHECKERS.get(rule_type)
    if not checker:
        return []
    return checker(db, website_id, config)
