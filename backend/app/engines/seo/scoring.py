"""Page health scoring: weighted deduction from 100."""

SEVERITY_WEIGHT = {"critical": 25, "warning": 10, "info": 3}


def score_page(findings: list[dict]) -> dict:
    score = 100
    for finding in findings:
        score -= SEVERITY_WEIGHT.get(finding.get("severity", "info"), 3)
    score = max(score, 0)
    if score >= 85:
        grade = "good"
    elif score >= 60:
        grade = "needs_work"
    else:
        grade = "poor"
    return {"score": score, "grade": grade, "issues": len(findings)}
