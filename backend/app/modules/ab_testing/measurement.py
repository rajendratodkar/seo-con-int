"""A/B test measurement engine.

Pulls Search Console data per variant's URL, computes aggregated metrics,
and uses a simple z-test for CTR difference to determine statistical
significance.  No external statistics library required.
"""
import math
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session


def fetch_sc_metrics_for_url(
    db: Session, website_id: int, url: str, start: str, end: str,
) -> dict:
    """Aggregate Search Console data for a URL over a date range."""
    row = db.execute(
        text(
            "SELECT COALESCE(SUM(clicks), 0) AS total_clicks, "
            "COALESCE(SUM(impressions), 0) AS total_impressions, "
            "CASE WHEN SUM(impressions) > 0 THEN CAST(SUM(clicks) AS REAL) / SUM(impressions) ELSE 0 END AS avg_ctr, "
            "CASE WHEN SUM(impressions) > 0 THEN SUM(position * impressions) / SUM(impressions) ELSE 0 END AS avg_position "
            "FROM search_console_data "
            "WHERE website_id = :wid AND page_url = :url AND date >= :start AND date <= :end"
        ),
        {"wid": website_id, "url": url, "start": start, "end": end},
    ).mappings().one_or_none()
    return dict(row) if row else {"total_clicks": 0, "total_impressions": 0, "avg_ctr": 0, "avg_position": 0}


def fetch_daily_sc_metrics(
    db: Session, website_id: int, url: str, start: str, end: str,
) -> list[dict]:
    """Get daily SC metrics for a URL."""
    rows = db.execute(
        text(
            "SELECT date, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
            "CASE WHEN SUM(impressions) > 0 THEN CAST(SUM(clicks) AS REAL) / SUM(impressions) ELSE 0 END AS ctr, "
            "CASE WHEN SUM(impressions) > 0 THEN SUM(position * impressions) / SUM(impressions) ELSE 0 END AS position "
            "FROM search_console_data "
            "WHERE website_id = :wid AND page_url = :url AND date >= :start AND date <= :end "
            "GROUP BY date ORDER BY date"
        ),
        {"wid": website_id, "url": url, "start": start, "end": end},
    ).mappings().all()
    return [dict(r) for r in rows]


def ctr_z_test(
    clicks_a: int, impressions_a: int,
    clicks_b: int, impressions_b: int,
) -> dict:
    """Two-proportion z-test for CTR difference.

    Returns z-statistic, p-value (two-tailed), and confidence level.
    """
    if impressions_a == 0 or impressions_b == 0:
        return {"z": 0, "p_value": 1.0, "confidence": 0}

    ctr_a = clicks_a / impressions_a
    ctr_b = clicks_b / impressions_b
    p_pool = (clicks_a + clicks_b) / (impressions_a + impressions_b)

    if p_pool == 0 or p_pool == 1:
        return {"z": 0, "p_value": 1.0, "confidence": 0}

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / impressions_a + 1 / impressions_b))
    if se == 0:
        return {"z": 0, "p_value": 1.0, "confidence": 0}

    z = (ctr_a - ctr_b) / se

    # Approximate two-tailed p-value using the error function approximation
    # (Abramowitz & Stegun approximation for normal CDF)
    p_value = _two_tailed_p(z)
    confidence = 1 - p_value

    return {"z": round(z, 4), "p_value": round(p_value, 6), "confidence": round(confidence, 4)}


def _two_tailed_p(z: float) -> float:
    """Approximate two-tailed p-value from z-score."""
    x = abs(z) / math.sqrt(2)
    # Approximation of erf(x)
    t = 1 / (1 + 0.3275911 * x)
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    erf_approx = 1 - poly * math.exp(-x * x)
    cdf = 0.5 * (1 + erf_approx)
    return max(0, min(1, 2 * (1 - cdf)))


def evaluate_test(control_metrics: dict, variant_metrics: dict, min_days: int) -> dict:
    """Evaluate whether a test has enough data to declare a winner.

    Returns winner, confidence, and detailed comparison.
    """
    c = control_metrics
    v = variant_metrics

    # Need minimum days of data
    c_days = c.get("days", 0) if "days" in c else 0
    v_days = v.get("days", 0) if "days" in v else 0
    min_data_days = min(c_days, v_days)

    if min_data_days < min_days:
        return {
            "winner": "insufficient_data",
            "confidence": 0,
            "days_collected": min_data_days,
            "min_days_required": min_days,
        }

    # Run z-test on CTR
    c_clicks = c.get("total_clicks", 0)
    c_imp = c.get("total_impressions", 0)
    v_clicks = v.get("total_clicks", 0)
    v_imp = v.get("total_impressions", 0)

    test_result = ctr_z_test(c_clicks, c_imp, v_clicks, v_imp)

    # Need minimum impressions for meaningful results
    if c_imp < 100 or v_imp < 100:
        return {
            "winner": "insufficient_data",
            "confidence": 0,
            "reason": f"Need more impressions (control: {c_imp:,}, variant: {v_imp:,})",
            "days_collected": min_data_days,
            "min_days_required": min_days,
        }

    # Determine winner
    ctr_diff_pct = ((v.get("avg_ctr", 0) - c.get("avg_ctr", 0)) / c.get("avg_ctr", 1)) * 100 if c.get("avg_ctr", 0) > 0 else 0

    if test_result["confidence"] >= 0.95:
        if ctr_diff_pct > 0:
            winner = "variant"
        elif ctr_diff_pct < 0:
            winner = "control"
        else:
            winner = "inconclusive"
    elif test_result["confidence"] >= 0.90:
        # Approaching significance
        winner = "variant" if ctr_diff_pct > 0 else "control"
    else:
        winner = "inconclusive"

    return {
        "winner": winner,
        "confidence": test_result["confidence"],
        "z_score": test_result["z"],
        "p_value": test_result["p_value"],
        "control": {
            "clicks": c_clicks,
            "impressions": c_imp,
            "ctr": round(c.get("avg_ctr", 0) * 100, 2),
            "position": round(c.get("avg_position", 0), 1),
            "days": c_days,
        },
        "variant": {
            "clicks": v_clicks,
            "impressions": v_imp,
            "ctr": round(v.get("avg_ctr", 0) * 100, 2),
            "position": round(v.get("avg_position", 0), 1),
            "days": v_days,
        },
        "ctr_diff_pct": round(ctr_diff_pct, 2),
        "days_collected": min_data_days,
        "min_days_required": min_days,
    }
