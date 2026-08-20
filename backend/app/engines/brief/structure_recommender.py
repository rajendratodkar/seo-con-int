"""Structure recommender — suggests outline, word count, and section priorities.

Uses competitor analysis and SERP data to recommend optimal content structure.
"""
import json
from collections import Counter


def recommend_structure(
    competitors: list[dict],
    serp_data: dict,
    keyword: str,
) -> dict:
    """Generate a recommended content structure based on analysis data.

    Returns suggested outline, target word count, section priorities,
    and internal link anchor suggestions.
    """
    if not competitors:
        return _default_structure(keyword)

    # --- Target word count ---
    word_counts = [c["word_count"] for c in competitors if c.get("word_count", 0) > 0]
    if word_counts:
        avg_wc = sum(word_counts) / len(word_counts)
        max_wc = max(word_counts)
        # Target slightly above average, but not more than max competitor
        target_wc = min(int(avg_wc * 1.15), max_wc)
        target_wc = max(target_wc, 1500)  # minimum 1500 words for comprehensive content
    else:
        target_wc = 2000

    # --- Heading frequency analysis ---
    all_headings = []
    for c in competitors:
        for h in c.get("headings", []):
            all_headings.append(h["text"].lower().strip())

    heading_freq = Counter(all_headings)

    # Extract common section themes
    common_sections = []
    seen = set()
    for heading, count in heading_freq.most_common(20):
        # Deduplicate similar headings
        normalized = heading[:30]
        if normalized not in seen and count >= 2:
            seen.add(normalized)
            common_sections.append({
                "heading": heading.title(),
                "frequency": count,
                "total_competitors": len(competitors),
            })

    # --- Build suggested outline ---
    outline = _build_outline(keyword, common_sections, serp_data)

    # --- Section priorities ---
    priorities = _assign_priorities(outline, serp_data)

    # --- Internal link anchors ---
    internal_links = _suggest_anchors(keyword, outline)

    # --- Things to avoid ---
    things_to_avoid = _detect_patterns_to_avoid(competitors)

    return {
        "target_word_count": target_wc,
        "outline": outline,
        "section_priorities": priorities,
        "internal_link_anchors": internal_links,
        "things_to_avoid": things_to_avoid,
        "competitor_stats": {
            "avg_word_count": int(sum(word_counts) / len(word_counts)) if word_counts else 0,
            "min_word_count": min(word_counts) if word_counts else 0,
            "max_word_count": max(word_counts) if word_counts else 0,
            "competitors_with_faq": sum(1 for c in competitors if c.get("has_faq")),
            "competitors_with_schema": sum(1 for c in competitors if c.get("has_schema")),
            "avg_media_count": round(
                sum(c.get("media_count", 0) for c in competitors) / len(competitors), 1
            ) if competitors else 0,
        },
    }


def _build_outline(keyword: str, common_sections: list[dict], serp_data: dict) -> list[dict]:
    """Build a suggested H2/H3 outline."""
    outline = []

    # Title
    outline.append({
        "heading": keyword.title(),
        "level": 1,
        "priority": "critical",
        "notes": "Primary keyword in title",
    })

    # Introduction
    outline.append({
        "heading": "Introduction",
        "level": 2,
        "priority": "critical",
        "notes": "Hook + what the reader will learn",
    })

    # Add common sections from competitors
    added = set()
    for section in common_sections[:12]:
        heading = section["heading"]
        if heading.lower() not in added and heading.lower() != keyword.lower():
            outline.append({
                "heading": heading,
                "level": 2,
                "priority": "high" if section["frequency"] >= 3 else "medium",
                "notes": f"Found in {section['frequency']}/{section['total_competitors']} competitors",
            })
            added.add(heading.lower())

    # FAQ section if PAA detected
    paa = [f for f in serp_data.get("features_detected", []) if f["type"] == "people_also_ask"]
    if paa:
        outline.append({
            "heading": "Frequently Asked Questions",
            "level": 2,
            "priority": "high",
            "notes": "People Also Ask detected — answer common questions",
        })

    # Conclusion
    outline.append({
        "heading": "Conclusion",
        "level": 2,
        "priority": "high",
        "notes": "Summary + CTA",
    })

    return outline


def _assign_priorities(outline: list[dict], serp_data: dict) -> list[dict]:
    """Assign priority scores to each section."""
    return [
        {
            "heading": item["heading"],
            "priority": item["priority"],
            "reason": item.get("notes", ""),
        }
        for item in outline
        if item["level"] <= 2
    ]


def _suggest_anchors(keyword: str, outline: list[dict]) -> list[dict]:
    """Suggest internal link anchor text based on the outline."""
    anchors = []
    kw_words = keyword.split()

    for item in outline:
        if item["level"] == 2 and item["heading"] not in ("Introduction", "Conclusion"):
            # Create anchor variations
            anchor_text = item["heading"].lower()
            anchors.append({
                "anchor": anchor_text,
                "target_section": item["heading"],
                "reason": f"Link to '{item['heading']}' section from related content",
            })

    return anchors[:10]


def _detect_patterns_to_avoid(competitors: list[dict]) -> list[str]:
    """Detect common anti-patterns in competitor content."""
    avoid = []

    # Thin content
    thin = [c for c in competitors if c.get("word_count", 0) < 800]
    if thin:
        avoid.append(f"{len(thin)} competitor(s) have thin content (< 800 words) — aim for comprehensive coverage")

    # Low media
    no_media = [c for c in competitors if c.get("media_count", 0) == 0]
    if len(no_media) > len(competitors) * 0.5:
        avoid.append("Most competitors lack images — differentiate with visual content")

    # No FAQ
    no_faq = [c for c in competitors if not c.get("has_faq")]
    if len(no_faq) > len(competitors) * 0.7:
        avoid.append("Most competitors lack FAQ sections — add one to capture PAA snippets")

    # No schema
    no_schema = [c for c in competitors if not c.get("has_schema")]
    if len(no_schema) > len(competitors) * 0.7:
        avoid.append("Most competitors lack structured data — add FAQ/Article schema for rich snippets")

    return avoid


def _default_structure(keyword: str) -> dict:
    """Fallback structure when no competitor data is available."""
    return {
        "target_word_count": 2000,
        "outline": [
            {"heading": keyword.title(), "level": 1, "priority": "critical", "notes": "Primary keyword"},
            {"heading": "Introduction", "level": 2, "priority": "critical", "notes": "Hook + overview"},
            {"heading": f"What is {keyword}?", "level": 2, "priority": "high", "notes": "Definition and context"},
            {"heading": f"How to Use {keyword}", "level": 2, "priority": "high", "notes": "Practical guide"},
            {"heading": f"Benefits of {keyword}", "level": 2, "priority": "medium", "notes": "Value proposition"},
            {"heading": "Best Practices", "level": 2, "priority": "medium", "notes": "Expert tips"},
            {"heading": "Common Mistakes", "level": 2, "priority": "medium", "notes": "Pitfalls to avoid"},
            {"heading": "Frequently Asked Questions", "level": 2, "priority": "high", "notes": "FAQ for PAA"},
            {"heading": "Conclusion", "level": 2, "priority": "high", "notes": "Summary + CTA"},
        ],
        "section_priorities": [],
        "internal_link_anchors": [],
        "things_to_avoid": ["No competitor data available — follow general SEO best practices"],
        "competitor_stats": {},
    }
