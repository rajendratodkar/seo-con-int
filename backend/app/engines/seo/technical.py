"""Image ALT checks (IMG-001)."""
import json


def check_images(page: dict, content: dict | None) -> list[dict]:
    images = json.loads(content["images"]) if content and content.get("images") else []
    if not images:
        return []
    missing = [img for img in images if not img.get("alt")]
    if missing:
        return [{
            "rule_code": "IMG-001",
            "recommendation": "Add ALT text to content images",
            "why": "ALT attributes make images understandable to search engines and assistive tech.",
            "evidence": f"{len(missing)} of {len(images)} images missing ALT",
            "data": {"missing": len(missing), "total": len(images)},
            "severity": "info",
            "confidence": "high",
        }]
    return []
