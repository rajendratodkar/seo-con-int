"""Content gap engine.

Compares competitor keywords against our Search Console data to find:
- Keywords competitors rank for that we don't → new_content
- Keywords where we rank lower → improve_existing
- Keywords where we're close (positions 6-20) → quick_win
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def _normalize(kw: str) -> str:
    import re
    return re.sub(r"\s+", " ", kw.strip().lower())


def compute_gaps(
    db: Session, website_id: int, competitor_id: int,
) -> list[dict]:
    """Find content gaps between a competitor and our site.

    Returns a list of gap dicts ready for upsert.
    """
    # Get the competitor's keywords and positions
    comp_rankings = db.execute(
        text(
            "SELECT normalized, keyword, position, url "
            "FROM competitor_rankings WHERE competitor_id = :cid "
            "ORDER BY position ASC"
        ),
        {"cid": competitor_id},
    ).mappings().all()

    if not comp_rankings:
        return []

    # Get our keywords and best positions from Search Console
    our_keywords = {
        r.normalized: r.best_pos
        for r in db.execute(
            text(
                "SELECT LOWER(TRIM(query)) AS normalized, MIN(position) AS best_pos "
                "FROM search_console_data "
                "WHERE website_id = :wid AND query IS NOT NULL "
                "GROUP BY normalized"
            ),
            {"wid": website_id},
        ).mappings().all()
    }

    gaps = []
    for cr in comp_rankings:
        norm = cr.normalized
        comp_pos = cr.position
        our_pos = our_keywords.get(norm)

        # Determine opportunity type
        if our_pos is None:
            # We don't rank for this keyword at all
            opportunity = "new_content"
            our_position = None
        elif our_pos > comp_pos + 5:
            # We rank significantly lower
            opportunity = "improve_existing"
            our_position = our_pos
        elif 6 <= our_pos <= 20:
            # We're in striking distance (positions 6-20)
            opportunity = "quick_win"
            our_position = our_pos
        elif our_pos <= comp_pos:
            # We already rank better — skip
            continue
        else:
            # We rank slightly lower
            opportunity = "improve_existing"
            our_position = our_pos

        # Compute priority score (0..1)
        priority = _compute_priority(comp_pos, our_position, opportunity)

        gaps.append({
            "keyword": cr.keyword,
            "competitor_pos": comp_pos,
            "competitor_url": cr.url,
            "our_position": our_position,
            "opportunity": opportunity,
            "search_volume": None,  # Would need external API for this
            "priority": priority,
        })

    # Sort by priority descending
    gaps.sort(key=lambda g: -g["priority"])
    return gaps


def _compute_priority(
    comp_pos: float, our_pos: float | None, opportunity: str,
) -> float:
    """Compute a 0-1 priority score for a content gap.

    Higher = more valuable to act on.
    """
    score = 0.0

    # Base score from competitor position (lower position = more valuable keyword)
    if comp_pos <= 3:
        score += 0.4  # Top 3 — very valuable keyword
    elif comp_pos <= 10:
        score += 0.3
    elif comp_pos <= 20:
        score += 0.2
    else:
        score += 0.1

    # Opportunity boost
    if opportunity == "quick_win":
        score += 0.3  # High chance of success
    elif opportunity == "new_content":
        score += 0.2  # Good potential but more work
    elif opportunity == "improve_existing":
        score += 0.15

    # If we don't rank at all, slightly higher priority (greenfield)
    if our_pos is None:
        score += 0.1

    return min(1.0, score)
