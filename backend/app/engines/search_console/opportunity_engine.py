"""Search Console opportunity detection (data-based recommendations).

Classic strike zone: high impressions, position 4-12, below-average CTR.
These are the strongest 'Improve Article' signals — pure data, high confidence.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

MIN_IMPRESSIONS = 500
POSITION_MIN = 4.0
POSITION_MAX = 12.0


def find_page_opportunities(db: Session, website_id: int, days: int = 28, limit: int = 25) -> list[dict]:
    rows = db.execute(
        text(
            "SELECT page_url, SUM(clicks) AS clicks, SUM(impressions) AS impressions, "
            "AVG(position) AS avg_position, "
            "CASE WHEN SUM(impressions) > 0 THEN CAST(SUM(clicks) AS REAL) / SUM(impressions) ELSE 0 END AS ctr "
            "FROM search_console_data "
            "WHERE website_id = :website_id AND page_url IS NOT NULL "
            "AND date >= date('now', :days) "
            "GROUP BY page_url "
            "HAVING SUM(impressions) >= :min_impressions "
            "AND AVG(position) BETWEEN :pmin AND :pmax "
            "ORDER BY SUM(impressions) DESC LIMIT :limit"
        ),
        {
            "website_id": website_id,
            "days": f"-{days} days",
            "min_impressions": MIN_IMPRESSIONS,
            "pmin": POSITION_MIN,
            "pmax": POSITION_MAX,
            "limit": limit,
        },
    ).mappings().all()

    opportunities = []
    for row in rows:
        opportunities.append({
            "page_url": row["page_url"],
            "recommendation": "Improve Article",
            "why": "High impressions with a ranking opportunity — page sits on the cusp of top positions.",
            "evidence": (
                f"{row['impressions']:,} impressions · Position {row['avg_position']:.1f} · CTR {row['ctr'] * 100:.2f}%"
            ),
            "data": {
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "avg_position": round(row["avg_position"], 1),
                "ctr": round(row["ctr"], 4),
                "window_days": days,
            },
            "confidence": "high",
            "severity": "warning" if row["impressions"] >= 5000 else "info",
        })
    return opportunities
