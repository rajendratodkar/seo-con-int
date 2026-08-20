"""Structured data checks (SD-001): JSON-LD validity and required properties."""
import json

TYPE_REQUIRED = {
    "article": ["headline"],
    "blogposting": ["headline"],
    "product": ["name"],
    "faqpage": ["mainEntity"],
    "organization": ["name"],
}


def check_structured_data(page: dict, content: dict | None) -> list[dict]:
    raw = (content or {}).get("schema_json")
    if not raw:
        return []
    try:
        blocks = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return [{
            "rule_code": "SD-001",
            "recommendation": "Fix invalid JSON-LD structured data",
            "why": "Unparseable JSON-LD is ignored by search engines.",
            "evidence": "JSON-LD block failed to parse",
            "data": {},
            "severity": "warning",
            "confidence": "high",
        }]

    issues = []
    for block in blocks if isinstance(blocks, list) else [blocks]:
        graph = block.get("@graph", [block]) if isinstance(block, dict) else [block]
        for node in graph:
            if not isinstance(node, dict):
                continue
            node_type = str(node.get("@type", "")).lower()
            required = TYPE_REQUIRED.get(node_type)
            if required and any(not node.get(prop) for prop in required):
                issues.append(f"{node_type} missing {required}")
    if issues:
        return [{
            "rule_code": "SD-001",
            "recommendation": "Complete required structured data properties",
            "why": "Missing required properties make rich results ineligible.",
            "evidence": "; ".join(issues[:3]),
            "data": {"issues": issues[:10]},
            "severity": "warning",
            "confidence": "high",
        }]
    return []
