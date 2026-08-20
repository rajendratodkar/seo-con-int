"""Boot smoke test: app starts, schema applies, routes register."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

app = create_app()
with TestClient(app) as client:
    health = client.get("/api/health/")
    print("health:", health.status_code, health.json())
    assert health.json()["database"] == "ok"

    # Spot-check one endpoint per module family
    checks = [
        "/api/websites/", "/api/references/", "/api/findings/?website_id=1",
        "/api/research/sources", "/api/content-ideas/", "/api/keywords/?website_id=1",
        "/api/discussions/", "/api/settings/values", "/api/settings/ai-providers",
        "/api/article-plans/", "/api/topic-clusters/?website_id=1",
        "/api/internal-links/?website_id=1", "/api/reports/weekly?website_id=1",
        "/api/content-audit/?website_id=1", "/api/opportunities/?website_id=1",
        "/api/content/drafts", "/api/publishing/logs",
        "/api/publishing/config/wordpress", "/api/publishing/config/github",
        "/api/google-analytics/connection?website_id=1",
        "/api/diagnostics/events", "/api/diagnostics/info",
        "/api/monitoring/channels", "/api/monitoring/rules",
        "/api/ab-tests",
        "/api/competitors?website_id=1", "/api/competitors/gaps/stats?website_id=1",
        "/api/content-briefs?website_id=1",
        "/api/content-refresh/stats?website_id=1",
    ]
    failures = 0
    for path in checks:
        r = client.get(path)
        marker = "OK " if r.status_code == 200 else "FAIL"
        if r.status_code != 200:
            failures += 1
            print(f"{marker} {r.status_code} {path} -> {r.text[:200]}")
        else:
            print(f"{marker} {r.status_code} {path}")

    routes = sorted({getattr(r, "path", "") for r in app.routes})
    print(f"\nTotal routes registered: {len(routes)}")
    sys.exit(1 if failures else 0)
