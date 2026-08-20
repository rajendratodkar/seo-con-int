"""Content checks: H1 structure, thin content, keyword stuffing (H-001, CNT-001, SPM-001)."""
import json
from collections import Counter

THIN_CONTENT_WORDS = 300
STUFFING_THRESHOLD = 0.045  # single-term frequency above 4.5% of all words


def check_content(page: dict, content: dict | None) -> list[dict]:
    findings = []
    headings = json.loads(content["headings"]) if content and content.get("headings") else []
    h1_count = sum(1 for h in headings if h.get("level") == 1)
    if h1_count != 1:
        findings.append({
            "rule_code": "H-001",
            "recommendation": "Use exactly one H1 heading",
            "why": "A single H1 clarifies the page's primary topic.",
            "evidence": f"Found {h1_count} H1 headings",
            "data": {"h1_count": h1_count},
            "severity": "info",
            "confidence": "high",
        })

    word_count = (content or {}).get("word_count") or 0
    if word_count and word_count < THIN_CONTENT_WORDS:
        findings.append({
            "rule_code": "CNT-001",
            "recommendation": "Expand thin content",
            "why": f"Only {word_count} words — below the {THIN_CONTENT_WORDS}-word thin-content threshold.",
            "evidence": f"Word count: {word_count}",
            "data": {"word_count": word_count},
            "severity": "warning",
            "confidence": "medium",
        })

    text = ((content or {}).get("text_content") or "").lower()
    words = [w for w in text.split() if len(w) > 3]
    if len(words) > 200:
        term, count = Counter(words).most_common(1)[0]
        frequency = count / len(words)
        if frequency > STUFFING_THRESHOLD:
            findings.append({
                "rule_code": "SPM-001",
                "recommendation": "Reduce keyword repetition",
                "why": f"'{term}' appears in {frequency:.1%} of all words — unnatural repetition.",
                "evidence": f"'{term}' x{count} of {len(words)} words",
                "data": {"term": term, "count": count, "frequency": round(frequency, 4)},
                "severity": "warning",
                "confidence": "medium",
            })
    return findings
