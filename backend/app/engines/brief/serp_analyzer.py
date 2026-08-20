"""SERP feature analyzer — infers SERP features from Search Console query patterns.

No external API calls; uses SC data patterns and heuristics.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def detect_serp_features(db: Session, website_id: int, keyword: str, days: int = 28) -> dict:
    """Analyze Search Console data for a keyword to infer SERP feature presence."""
    # Gather SC data for the keyword and similar queries
    rows = db.execute(
        text(
            "SELECT query, page_url, clicks, impressions, ctr, position "
            "FROM search_console_data "
            "WHERE website_id = :w AND query IS NOT NULL "
            "AND LOWER(query) LIKE :pattern "
            "AND date >= date('now', :days) "
            "ORDER BY impressions DESC LIMIT 100"
        ),
        {"w": website_id, "pattern": f"%{keyword.lower()}%", "days": f"-{days} days"},
    ).mappings().all()

    if not rows:
        return {
            "features_detected": [],
            "query_volume": 0,
            "unique_pages": 0,
            "avg_position": 0,
            "dominant_intent": "unknown",
            "queries": [],
        }

    queries = [dict(r) for r in rows]
    total_impressions = sum(q["impressions"] for q in queries)
    unique_pages = len(set(q["page_url"] for q in queries if q["page_url"]))
    avg_position = (
        sum(q["position"] * q["impressions"] for q in queries) / total_impressions
        if total_impressions else 0
    )

    features = []

    # Featured snippet detection: position ≤ 3 with high CTR
    top_results = [q for q in queries if q["position"] <= 3]
    if top_results:
        avg_top_ctr = sum(q["ctr"] for q in top_results) / len(top_results)
        if avg_top_ctr > 0.15:
            features.append({
                "type": "featured_snippet",
                "confidence": min(avg_top_ctr * 5, 0.95),
                "note": f"High CTR ({avg_top_ctr:.0%}) at top positions suggests featured snippet",
            })

    # PAA (People Also Ask) detection: question-pattern queries
    question_words = ("how", "what", "why", "when", "where", "who", "which", "is", "can", "does", "do")
    question_queries = [
        q for q in queries
        if any(q["query"].lower().startswith(w) for w in question_words)
    ]
    if len(question_queries) >= 2:
        features.append({
            "type": "people_also_ask",
            "confidence": min(len(question_queries) / 5, 0.9),
            "note": f"{len(question_queries)} question-pattern queries detected",
            "sample_questions": [q["query"] for q in question_queries[:5]],
        })

    # Knowledge panel detection: single dominant page with very high impressions
    if unique_pages >= 1:
        page_impressions = {}
        for q in queries:
            if q["page_url"]:
                page_impressions[q["page_url"]] = page_impressions.get(q["page_url"], 0) + q["impressions"]
        if page_impressions:
            top_page_imp = max(page_impressions.values())
            if total_impressions > 0 and top_page_imp / total_impressions > 0.6:
                features.append({
                    "type": "knowledge_panel",
                    "confidence": min(top_page_imp / total_impressions, 0.85),
                    "note": "Single page dominates impressions — likely knowledge panel",
                })

    # Video carousel detection: YouTube URLs in top results
    youtube_pages = [q for q in queries if q["page_url"] and "youtube.com" in q["page_url"]]
    if youtube_pages:
        features.append({
            "type": "video_carousel",
            "confidence": min(len(youtube_pages) / 3, 0.8),
            "note": f"{len(youtube_pages)} YouTube results in top queries",
        })

    # Image pack detection: multiple pages from same domain (often images section)
    if unique_pages >= 5:
        features.append({
            "type": "image_pack",
            "confidence": 0.4,
            "note": "Multiple diverse pages suggest image pack may be present",
        })

    # Infer search intent from query patterns
    intent = _infer_intent(queries, keyword)

    return {
        "features_detected": features,
        "query_volume": total_impressions,
        "unique_pages": unique_pages,
        "avg_position": round(avg_position, 1),
        "dominant_intent": intent,
        "queries": queries[:20],
    }


def _infer_intent(queries: list[dict], keyword: str) -> str:
    """Infer the dominant search intent from query patterns."""
    kw = keyword.lower()
    intent_signals = {
        "informational": 0,
        "navigational": 0,
        "transactional": 0,
        "commercial": 0,
    }

    info_words = ("how to", "what is", "guide", "tutorial", "learn", "explain", "tips", "examples")
    nav_words = ("login", "sign in", "official", "website", "homepage", "app")
    trans_words = ("buy", "price", "cost", "cheap", "deal", "discount", "order", "subscribe")
    comm_words = ("best", "top", "review", "comparison", "vs", "alternative", "comparison")

    for q in queries:
        query = q["query"].lower()
        if any(w in query for w in info_words):
            intent_signals["informational"] += q["impressions"]
        elif any(w in query for w in nav_words):
            intent_signals["navigational"] += q["impressions"]
        elif any(w in query for w in trans_words):
            intent_signals["transactional"] += q["impressions"]
        elif any(w in query for w in comm_words):
            intent_signals["commercial"] += q["impressions"]
        else:
            # Default: informational for most SEO queries
            intent_signals["informational"] += q["impressions"] * 0.5
            intent_signals["commercial"] += q["impressions"] * 0.5

    if max(intent_signals.values()) == 0:
        return "informational"

    return max(intent_signals, key=intent_signals.get)
