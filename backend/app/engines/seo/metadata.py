"""Metadata checks: title, meta description, canonical (rules META-001..003)."""


def check_metadata(page: dict, content: dict | None) -> list[dict]:
    findings = []
    title = page.get("title") or ""
    if not title:
        findings.append({
            "rule_code": "META-001",
            "recommendation": "Add a title tag",
            "why": "The page has no title tag, which is required for indexing and click-through.",
            "evidence": "No <title> element found during crawl",
            "data": {},
            "severity": "warning",
            "confidence": "high",
        })
    elif not (30 <= len(title) <= 60):
        findings.append({
            "rule_code": "META-001",
            "recommendation": "Resize the title tag to 30-60 characters",
            "why": "Titles outside this range are typically truncated or rewritten in search results.",
            "evidence": f"Title is {len(title)} characters",
            "data": {"title_length": len(title)},
            "severity": "info",
            "confidence": "high",
        })

    if not page.get("meta_description"):
        findings.append({
            "rule_code": "META-002",
            "recommendation": "Add a meta description",
            "why": "A meta description improves click-through from search results.",
            "evidence": "No meta description found during crawl",
            "data": {},
            "severity": "info",
            "confidence": "high",
        })

    if not page.get("canonical_url"):
        findings.append({
            "rule_code": "META-003",
            "recommendation": "Add a canonical tag",
            "why": "Canonicals prevent duplicate-content dilution.",
            "evidence": "No canonical link found during crawl",
            "data": {},
            "severity": "warning",
            "confidence": "high",
        })
    return findings
