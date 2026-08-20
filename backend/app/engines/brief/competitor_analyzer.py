"""Competitor content analyzer — extracts structure and patterns from top-ranking pages.

Uses crawled page data (already stored in the database) to analyze competitors.
"""
import json
import re
from sqlalchemy import text
from sqlalchemy.orm import Session


def analyze_competitors(db: Session, website_id: int, keyword: str, limit: int = 10) -> list[dict]:
    """Find and analyze top-ranking competitor pages for a keyword.

    Uses Search Console data to identify top pages, then pulls crawled content.
    """
    # Find top pages ranking for this keyword
    page_urls = db.execute(
        text(
            "SELECT page_url, AVG(position) AS avg_pos, SUM(impressions) AS impressions, "
            "SUM(clicks) AS clicks "
            "FROM search_console_data "
            "WHERE website_id = :w AND query IS NOT NULL "
            "AND LOWER(query) LIKE :pattern "
            "AND page_url IS NOT NULL "
            "AND date >= date('now', '-28 days') "
            "GROUP BY page_url "
            "ORDER BY impressions DESC "
            "LIMIT :lim"
        ),
        {"w": website_id, "pattern": f"%{keyword.lower()}%", "lim": limit},
    ).mappings().all()

    competitors = []
    for row in page_urls:
        url = row["page_url"]
        analysis = _analyze_page_content(db, url)
        if analysis:
            analysis["sc_data"] = {
                "avg_position": round(row["avg_pos"], 1),
                "impressions": row["impressions"],
                "clicks": row["clicks"],
            }
            competitors.append(analysis)

    return competitors


def _analyze_page_content(db: Session, url: str) -> dict | None:
    """Analyze a single page's crawled content for structure and patterns."""
    page = db.execute(
        text("SELECT * FROM pages WHERE url = :url LIMIT 1"),
        {"url": url},
    ).mappings().first()

    if not page:
        return None

    content_row = db.execute(
        text("SELECT * FROM page_content WHERE page_id = :pid LIMIT 1"),
        {"pid": page["id"]},
    ).mappings().first()

    if not content_row:
        return None

    title = page.get("title") or ""
    meta_desc = content_row.get("meta_description") or ""
    body_html = content_row.get("body_html") or ""
    body_text = _strip_html(body_html)

    # Extract headings
    headings = _extract_headings(body_html)

    # Word count
    words = body_text.split()
    word_count = len(words)

    # Keyword density
    kw_lower = keyword_from_url(url)  # rough fallback
    keyword_count = body_text.lower().count(kw_lower) if kw_lower else 0
    keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

    # Media count
    media_count = body_html.lower().count("<img")

    # FAQ detection
    has_faq = any(
        term in body_text.lower()
        for term in ("frequently asked", "faq", "common questions", "q&a")
    )

    # Schema detection
    has_schema = bool(re.search(r'"@type"\s*:', body_html))

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "word_count": word_count,
        "headings": headings,
        "keyword_density": round(keyword_density, 2),
        "media_count": media_count,
        "has_faq": has_faq,
        "has_schema": has_schema,
    }


def _extract_headings(html: str) -> list[dict]:
    """Extract H2/H3 headings from HTML."""
    headings = []
    for match in re.finditer(r"<(h[2-3])[^>]*>(.*?)</\1>", html, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1)[1])
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if text:
            headings.append({"level": level, "text": text})
    return headings


def _strip_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_from_url(url: str) -> str:
    """Extract a rough keyword from URL slug."""
    path = url.rstrip("/").split("/")[-1]
    return path.replace("-", " ").replace("_", " ")
