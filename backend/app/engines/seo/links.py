"""Internal link checks (LNK-001): internal links pointing at non-existent pages."""


def check_links(page: dict, links: list[dict], all_page_urls: set[str]) -> list[dict]:
    broken = [
        link for link in links
        if link.get("is_internal") and link.get("target_url") not in all_page_urls
    ]
    if not broken:
        return []
    return [{
        "rule_code": "LNK-001",
        "recommendation": "Fix internal links that resolve to no known page",
        "why": "Internal links to missing pages waste crawl budget and hurt user experience.",
        "evidence": f"{len(broken)} internal link targets not found in crawled inventory",
        "data": {"targets": [link["target_url"] for link in broken[:10]]},
        "severity": "critical",
        "confidence": "medium",
    }]
