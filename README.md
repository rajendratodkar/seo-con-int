# SEO Content Intelligence

A Windows desktop app that connects your website + Google Search Console, analyzes
your content against evidence-based SEO rules, and turns real data into research,
content ideas, briefs, and AI-assisted drafts — with **every recommendation
explainable** (What · Why · Evidence · Confidence).

**Stack:** Tauri (Rust shell) · React 18 + TypeScript + Vite · Python FastAPI · SQLite

---

## Principles (the 7 rules)

1. One responsibility per module.
2. No duplicate engines — `engines/` owns analysis.
3. API integration ≠ business logic.
4. Database ≠ analysis (verdicts/scores are computed live, never stored as facts).
5. AI ≠ truth — every AI output is labeled `ai_suggestion`.
6. Every recommendation has What · Why · Evidence · Confidence · Action.
7. Raw data is never overwritten (`raw → normalized → analysis`).

Full design: [plan.md](plan.md) · Task tracker: [todo.md](todo.md) ·
Architecture docs: [docs/architecture/](docs/architecture/) ·
Database design: [docs/database/](docs/database/)

---

## Repository layout

```
backend/    FastAPI app (modules/, engines/, integrations/, core/)
frontend/   React + TypeScript SPA (Vite)
desktop/    Tauri shell (spawns backend sidecar, hosts frontend)
database/   schema_v1.sql + 12 extension schemas (60+ tables)
data/       SQLite DB + raw/processed/exports/runtime (created at first run)
docs/       plan + architecture + database docs
scripts/    serve.py, boot_smoke.py, validate_schema.py, make_icons.ps1
tests/      pytest boot tests
config/     env-var based config notes
```

---

## Quick start

### 1. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run (binds 127.0.0.1:8317, applies schema + seeds on boot)
python scripts/backend/serve.py
```

Health check: `http://127.0.0.1:8317/api/health/` · API docs: `http://127.0.0.1:8317/docs`

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to the backend)
npm run build      # production bundle -> frontend/dist
```

### 3. Desktop app (Tauri)

Requires the Rust toolchain + WebView2. See [desktop/README.md](desktop/README.md).

```powershell
cd desktop/src-tauri
cargo install tauri-cli
cargo tauri dev
```

The shell spawns the Python backend, waits for `127.0.0.1:8317`, and kills it on exit.

---

## Configuration

Copy `.env.example` → `.env` (backend reads `SCI_*` variables). Notable:

| Variable | Purpose |
|---|---|
| `SCI_BACKEND_TOKEN` | Optional request token (middleware enforces when set) |
| `SCI_GOOGLE_CLIENT_ID` / `_SECRET` | Search Console OAuth |
| `SCI_OPENAI_API_KEY` / `SCI_GEMINI_API_KEY` / `SCI_ANTHROPIC_API_KEY` | AI providers (also configurable in-app, stored encrypted) |
| `SCI_WP_USER` / `SCI_WP_APP_PASSWORD`, `SCI_GITHUB_TOKEN` | Publishing targets (normally configured in-app under Drafts & Publishing, encrypted at rest) |

---

## Verification

```powershell
python scripts/database/validate_schema.py   # schema sanity
python scripts/backend/boot_smoke.py         # boot + endpoint smoke
pytest tests/ -q                             # boot tests
cd frontend; npm run build                   # type-check + bundle
```

---

## Status

All 30 phases are complete. See [todo.md](todo.md) for the full task tracker.

### Phase summary

| Phase | Name | Key deliverables |
|-------|------|------------------|
| 0 | Architecture | 33-table schema, FastAPI skeleton, DI pattern |
| 1 | Desktop foundation | Tauri shell, React+TS frontend, SQLite backend |
| 2 | Website connection | Crawler, platform detectors, sitemap parser |
| 3 | Search Console | OAuth, property discovery, historical + incremental import |
| 4 | SEO engine | Analyzer, scoring, technical/content/links/metadata, rule references |
| 5 | Recommendation engine | 9-field recommendations with What·Why·Evidence·Confidence·Action |
| 6 | Content audit | Verdicts (Keep·Improve·Refresh·Consolidate·Review) |
| 7 | Content Ideas | YouTube/Podcast/SC/News inputs, research + content gap analysis |
| 8 | Discussion | AI provider abstraction, chat + decision log grounded in research |
| 9 | Article Planner | Outline, evidence, intent, audience, internal links |
| 10 | AI drafting | Generated drafts, SEO check, fact-check, human approval gate |
| 11 | Advanced integrations | WordPress/GitHub publishing, GA, topic clusters, internal links |
| 12 | Desktop hardening | Auto-updates, deep linking, keychain, proxy, crash reporting |
| 13 | Bulk operations | Bulk crawl/analyze/ideas with background job tracking |
| 14 | Monitoring & Alerts | 5 checkers, 3 alerters (email/Slack/desktop), 15 endpoints |
| 15 | A/B Testing | Z-test measurement, 95% confidence, variant comparison |
| 16 | Competitor Analysis | Gap engine (new/improve/quick-win), rankings, competitor import |
| 17 | Analytics Dashboard | CSS-only charts, KPIs, period comparison, traffic/ranking data |
| 18 | Keyword Clustering | Jaccard similarity engine, auto-clustering from SC data |
| 19 | Schema Markup Builder | Article/FAQPage/HowTo/Product/BreadcrumbList/Organization generators |
| 20 | Content Calendar | Monthly grid + Kanban, pipeline management, deadlines |
| 21 | Backlink Monitor | Change tracking (gained/lost), profile analysis, CSV import |
| 22 | Page Speed Insights | SVG gauges, CWV thresholds (LCP/FID/CLS/FCP/TTFB) |
| 23 | Content Rewriter | Type-specific prompts, copy/select/apply, rewrite history |
| 24 | SEO Checklist | Auto-generate from findings + 13 standard items, 6 categories |
| 25 | Sitemap Generator | Configurable settings, URL overrides, valid XML output |
| 26 | Report Generator | Data collection + HTML rendering + PDF export |
| 27 | SERP Preview | Google-style card, live editor, real-time preview, tips |
| 28 | Redirect Manager | CRUD + bulk import (CSV), chain detection, check history |
| 29 | AI Content Brief Generator | SERP analysis, competitor insights, outline + FAQ generation |
| 30 | Content Refresh Scheduler | Staleness detection, trend analysis, priority scoring, refresh queue |

### Module count

- **Backend modules:** 35 (modules/, engines/, integrations/)
- **API endpoints:** 200+
- **Frontend pages:** 31 (including Settings)
- **Database tables:** 60+ across main schema + 12 extension schemas
- **Extension schemas:** monitoring, AB testing, competitors, calendar, backlinks, page speed, rewrites, checklist, sitemap, reports, rank tracker, SERP AB testing, content briefs, content refresh
