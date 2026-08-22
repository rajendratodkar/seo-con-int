# SEO Content Intelligence — TODO

> Master task list for building the project. Work top-to-bottom, one phase at a time.
> Check off items as they complete. **Never skip ahead within a phase.**

**Stack:** Tauri + React / TypeScript + Python + SQLite
**Rule of thumb:** Small steps · one phase at a time · no duplicate modules

---

## Progress Overview

| Phase | Name | Status |
|-------|------|--------|
| 0 | Architecture | ✅ Done |
| 1 | Desktop foundation | ✅ Done |
| 2 | Website connection | ✅ Done |
| 3 | Search Console | ✅ Done |
| 4 | SEO engine | ✅ Done |
| 5 | Recommendation engine ⭐ | ✅ Done |
| 6 | Content audit | ✅ Done |
| 7 | Content Ideas | ✅ Done |
| 8 | Discussion | ✅ Done |
| 9 | Article Planner | ✅ Done |
| 10 | AI drafting | ✅ Done |
| 11 | Advanced integrations | ✅ Done |
| 12 | Desktop production hardening | ✅ Done |
| 13 | Bulk operations | ✅ Done |
| 14 | Monitoring & Alerts | ✅ Done |
| 15 | A/B Testing | ✅ Done |
| 16 | Competitor Analysis | ✅ Done |
| 17 | Advanced Analytics Dashboard | ✅ Done |
| 18 | Keyword Clustering | ✅ Done |
| 19 | Schema Markup Builder | ✅ Done |
| 20 | Content Calendar | ✅ Done |
| 21 | Backlink Monitor | ✅ Done |
| 22 | Page Speed Insights | ✅ Done |
| 23 | Content Rewriter | ✅ Done |
| 24 | SEO Checklist | ✅ Done |
| 25 | Sitemap Generator | ✅ Done |
| 26 | Report Generator | ✅ Done |
| 27 | SERP Preview | ✅ Done |
| 28 | Redirect Manager | ✅ Done |
| 29 | AI Content Brief Generator ⭐ | ✅ Done |
| 30 | Content Refresh Scheduler | ✅ Done |
| 31 | Search Console File Upload | ✅ Done |
| 32 | URL Inspection Import | ✅ Done |
| 33 | Index Coverage Import | ✅ Done |
| 34 | Links Import | ✅ Done |

---

## Archived phases (0–28) — completed

| Phase | Summary |
|-------|---------|
| **0** | Architecture: 9 top-level folders, `backend/app/` subfolders, `schema_v1.sql` (33 tables, 30 indexes), FastAPI skeleton (`create_app()` + lifespan), DI pattern (`api/dependencies.py`), 30 frontend pages planned |
| **1** | Desktop: Tauri project (`desktop/src-tauri/`), React+TS frontend (Vite), FastAPI backend (`backend/app/main.py`), SQLite connection (`backend/app/database/connection.py`), Tauri→backend→frontend wiring (`main.rs` spawns `serve.py`), app icons |
| **2** | Websites: `websites/` module (schemas, repository, service, router, detectors), platform detectors (WordPress, Astro/static), `integrations/sitemap/`, `integrations/crawler/` (crawler.py + parser.py + robots.py), `pages/` module, test-connection action |
| **3** | Search Console: OAuth (`oauth.py`), property discovery, connect property, `api_client.py` (SC API queries), `importer.py` (historical + incremental), `normalizer.py` (raw→normalized, never overwrite raw), `analytics.py` (period comparison), SC page in UI |
| **4** | SEO engine: `engines/seo/` (analyzer, scoring, technical, content, links, metadata, structured_data), `engines/search_console/opportunity_engine.py`, `engines/content/` (drafting, markdown), `seo_analysis/` module (rules registry, evaluator, findings), `references/` module (listing, categories, rules lookup), seeded references (Google SEO, SC, Structured Data, Spam Policies, SEBI, AMFI, RBI, Income Tax, AMC) |
| **5** | Recommendations: 9-field recommendation objects (What·Why·Evidence·Data·Rule·Reference·Confidence·Severity·Action), data-based from SC, rule-based from SEO engine, AI labeled "AI suggestion", `seo_opportunities/` module + `Opportunities.tsx` |
| **6** | Content audit: `content_audit/` module, verdicts (Keep·Improve·Refresh·Consolidate·Review), verdict driven by SC data + SEO findings (computed live), Audit page with filters |
| **7** | Content Ideas: `content_ideas/` module (service: generate/validate/scoring), `integrations/youtube/` (extractor, metadata, transcript), `integrations/podcast/` (extractor, metadata), inputs (YouTube·Podcast·SC·Website·News·Manual), `research/` module (extract_topics/claims/questions, content_gap), Ideas page |
| **8** | Discussion: `integrations/ai/providers.py` (complete() dispatcher + _openai/_gemini/_anthropic), provider abstraction, `discussion/` module (messages, decisions), ground in stored research, hallucination control, Discussion page (chat + decision log) |
| **9** | Article Planner: `article_planner/` module (create_from_idea, _gather_evidence, _infer_intent, update_brief, mark_brief_ready), plan output (title, intent, audience, outline, questions, internal links, sources, facts, SC evidence, things to avoid), Article Planner page |
| **10** | AI drafting: `engines/content/drafting.py` (stored as `ai_suggestion`), `content/` module (generate_draft, edit, approve, reject), Drafts & Publishing page (`Drafts.tsx`), fact-check against [VERIFY:] placeholders, SEO check against rules engine, human approval gate |
| **11** | Integrations: WordPress (`integrations/wordpress/client.py` + `modules/publishing/`), GitHub/Astro (`integrations/github/client.py`), Google Analytics (`integrations/ga/client.py` + `modules/google_analytics/`), `topic_clusters/`, `internal_links/`, `reports/` (weekly) |
| **12** | Desktop hardening: Tauri auto-updates, deep linking (`sci://`), OS keychain token storage (`keyring`), proxy (`SCI_HTTP_PROXY`/`SCI_HTTPS_PROXY` in `app/core/http.py`), crash reporting, usage analytics (5k cap), rotating logs, file drag-and-drop, `diagnostics/` module |
| **13** | Bulk ops: `bulk_operations/` module, `POST /api/bulk/crawl`, `/analyze`, `/ideas`, job tracking (`GET /api/bulk/jobs`), background execution, validation (1–50 websites) |
| **14** | Monitoring: `schema_v1_monitoring.sql` (4 tables), `monitoring/` module (checkers, alerters), 5 checkers (ranking/traffic/CTR/crawl/errors), 3 alerters (email/Slack/desktop), 15 API endpoints, auto-loading extension schemas, Monitoring page (Channels/Rules/History tabs) |
| **15** | A/B Testing: `schema_v1_ab_testing.sql` (3 tables), `ab_testing/` module (measurement.py: z-test, 95% confidence), 9 API endpoints, A/B Testing page (create/start/collect/evaluate), results display (CTR, z-score, p-value, winner) |
| **16** | Competitor Analysis: `schema_v1_competitors.sql` (3 tables), `competitor_analysis/` module (gap_engine: new_content/improve_existing/quick_win), 12 API endpoints, Competitor Analysis page (add/import/rankings/gaps) |
| **17** | Analytics Dashboard: 6 analytics endpoints in `/api/reports/`, CSS-only charts (BarChart, Sparkline, HBar, KpiCard), Analytics page (4 tabs + period selector), KPIs (clicks, impressions, CTR, position, pages, queries) |
| **18** | Keyword Clustering: `keyword_clustering/` module (Jaccard similarity engine), auto-clustering from SC data, 10 API endpoints, Keyword Clusters page (create/auto-cluster/add/remove) |
| **19** | Schema Markup: `schema_markup/` module (generators.py: Article, FAQPage, HowTo, Product, BreadcrumbList, Organization), type-specific validation, 8 API endpoints, Schema Markup page (dynamic forms, validate, coverage stats) |
| **20** | Content Calendar: `schema_v1_calendar.sql`, `content_calendar/` module, 7 API endpoints (CRUD + pipeline + deadlines), Content Calendar page (monthly grid + Kanban) |
| **21** | Backlink Monitor: `schema_v1_backlinks.sql` (2 tables), `backlink_monitor/` module, change tracking (gained/lost), 8 API endpoints (CRUD + import + profile + changes), Backlinks page (KPIs, domains, CSV import) |
| **22** | Page Speed: `schema_v1_page_speed.sql`, `page_speed/` module, SVG score gauges, CWV thresholds (LCP/FID/CLS/FCP/TTFB), 5 API endpoints, Page Speed page (overview, scores, manual record) |
| **23** | Content Rewriter: `schema_v1_rewrites.sql`, `content_rewriter/` module, type-specific prompts (Title/Description/Heading/Custom), 5 API endpoints, Content Rewriter page (input, options, copy/select/apply, history) |
| **24** | SEO Checklist: `schema_v1_checklist.sql` (2 tables), `seo_checklist/` module, auto-generate from findings + 13 standard items, 6 categories, 9 API endpoints, SEO Checklist page (per-page, progress bars) |
| **25** | Sitemap Generator: `schema_v1_sitemap_gen.sql` (2 tables), `sitemap_generator/` module, settings (priority/changefreq/max/exclude), URL overrides, valid XML output, 7 API endpoints, Sitemap Generator page (settings, preview, download) |
| **26** | Report Generator: `schema_v1_reports.sql` (2 tables), `report_generator/` module, data collection + HTML rendering + PDF export (`xhtml2pdf`), 7 API endpoints, Reports page (list, generate, preview, HTML/PDF download) |
| **27** | SERP Preview: `serp_preview/` module, Google-style card rendering, title/description length limits, URL formatting, 5 API endpoints, SERP Preview page (live editor, page selector, real-time preview, tips) |
| **28** | Redirect Manager: `schema_v1_redirects.sql` (2 tables), `redirect_manager/` module, CRUD + validation, bulk import (CSV), chain detection, check history, 11 API endpoints, Redirects page (stats, filter tabs, table, modals) |

---

## Phase 29 — AI Content Brief Generator ⭐

> **Goal:** Given a target keyword, auto-generate a structured writing brief by
> combining Search Console data, competitor analysis, keyword clustering, and
> SERP features — then hand off to the Article Planner.

- [ ] `database/schema/schema_v1_content_briefs.sql`: tables (`content_briefs`, `brief_sections`, `brief_competitors`)
- [ ] `content_brief/` module: schemas, repository, service, router
- [ ] `engines/brief/`: serp_analyzer, competitor_analyzer, structure_recommender
- [ ] `serp_analyzer.py`: parse SERP features — PAA boxes, featured snippets, knowledge panels, video carousels, image packs
- [ ] `competitor_analyzer.py`: top-10 competitor content length, headings structure, keyword density, media usage
- [ ] `structure_recommender.py`: suggested outline (H2/H3 hierarchy), target word count, section priorities, internal link anchors
- [ ] AI-powered brief generation: title options, meta description drafts, FAQ suggestions, key talking points
- [ ] Brief output: target_keyword, primary_keyword, secondary_keywords, search_intent, target_word_count, outline, competitor_insights, serp_features, internal_links, faq, things_to_avoid, source_evidence
- [ ] Integration: pull from Search Console (impressions/clicks/CTR/position), keyword clusters, competitor rankings, and SERP data
- [ ] Save / edit / version briefs (auto-increment version on re-generate)
- [ ] Export brief as Markdown (structured sections ready for copy-paste into editor)
- [ ] 8 API endpoints under `/api/content-briefs/` (CRUD + generate + export + history)
- [ ] Frontend Content Briefs page: keyword input → generate → editable brief with competitor tabs → export → send to Article Planner
- [ ] **✅ Done when:** entering a keyword produces a data-driven, competitor-aware writing brief with outline, keywords, FAQ, and evidence links

---

## Standing Rules — check before every PR

- [x] One responsibility per module (no `x.py` + `x_engine.py` + `x_service.py` + `x_manager.py` without distinct duties)
- [x] No duplicate engines — `seo_analysis/` is the single owner of SEO analysis
- [x] API integration ≠ business logic (Google API separate from SEO analysis)
- [x] Database ≠ analysis (no calculations in models)
- [x] AI ≠ truth (label AI suggestions — `ai_suggestion` status on every draft)
- [x] Every recommendation has What · Why · Evidence · Source · Action
- [x] Raw data is never overwritten (`raw → normalized → analysis`)

---

## Undocumented modules (built but not in a numbered phase)

- [x] `rank_tracker/` module: schemas, repository, service, router — `schema_v1_rank_tracker.sql` (`tracked_keywords`, `keyword_daily_snapshots`, `keyword_alerts`)
- [x] `serp_ab_testing/` module: schemas, repository, service, router — `schema_v1_serp_ab.sql` (`serp_ab_tests`, `serp_ab_variants`, `serp_ab_daily_snapshots`)
- [x] Frontend pages: `RankTracker.tsx`, `SERPABTesting.tsx`

---

## Phase 30 — Content Refresh Scheduler

> **Goal:** Automatically detect stale content, score refresh urgency, and
> generate actionable update recommendations with priority dates.

- [x] `database/schema/schema_v1_content_refresh.sql`: tables (`refresh_rules`, `refresh_schedules`, `refresh_history`)
- [x] `content_refresh/` module: schemas, repository, service, router
- [x] `engines/refresh/`: staleness_detector, trend_analyzer, priority_scorer
- [x] `staleness_detector.py`: flag pages older than N days, pages with declining impressions/clicks, pages with outdated dates in metadata
- [x] `trend_analyzer.py`: compute 30/60/90-day trends per page — declining, stable, growing
- [x] `priority_scorer.py`: score pages by urgency (staleness × traffic decline × revenue potential)
- [x] Refresh recommendations: what to update (title, content, links, schema), when to update (priority date), why (stale content, traffic drop, competitor improvements)
- [x] Integration: pull page age from crawl dates, SC trends from search_console_data, findings from seo_findings
- [x] Configurable rules: minimum age threshold, traffic drop %, staleness weight
- [x] Refresh history: track which pages were refreshed, what changed, impact on metrics
- [x] 7 API endpoints under `/api/content-refresh/` (rules, schedule, history, run-scan, recommendations)
- [x] Frontend Content Refresh page: staleness dashboard (red/yellow/green), scan results, refresh queue, history log
- [x] **✅ Done when:** entering a website produces a prioritized list of pages to refresh with reasons and suggested changes

---

## Phase 31 — Search Console File Upload

> **Goal:** Allow users to import Search Console data from exported CSV/JSON files
> when OAuth connection is not available (e.g., shared computers, corporate
> restrictions, or manual data sharing).

### Search Console Data Types (from export)

Google Search Console exports provide the following data:

#### Performance Report (CSV)
| Column | Description | Example |
|--------|-------------|--------|
| Date | Data date | 2026-08-15 |
| Query | Search keyword | "seo best practices" |
| Page | Landing page URL | https://example.com/seo-guide |
| Clicks | Number of clicks | 142 |
| Impressions | Number of times shown | 5400 |
| CTR | Click-through rate (clicks/impressions) | 2.63% |
| Position | Average ranking position | 8.2 |

#### Performance Report (JSON - API format)
```json
{
  "rows": [
    {
      "keys": ["seo best practices", "https://example.com/seo-guide"],
      "clicks": 142,
      "impressions": 5400,
      "ctr": 0.0263,
      "position": 8.2
    }
  ]
}
```

#### URL Inspection (CSV)
| Column | Description |
|--------|-------------|
| URL | Page URL |
| Coverage | Verdict (Pass, Fail, Excluded) |
| Crawled as | Googlebot desktop/mobile |
| Crawl allowed | Yes/No |
| Page fetch | Successful/Failed |
| Indexing | Indexed/Not indexed |
| Last crawl | Date of last crawl |

#### Index Coverage (CSV)
| Column | Description |
|--------|-------------|
| Status | Error, Valid, Warning, Excluded |
| Category | Specific issue type |
| Count | Number of affected URLs |
| Examples | Sample URLs |

#### Links Report (CSV)
| Column | Description |
|--------|-------------|
| Target page | Your page URL |
| Source page | Linking page URL |
| Anchor text | Link text |
| First seen | When link was first detected |
| Last seen | Most recent detection |

### Implementation Tasks

- [x] `backend/app/modules/sc_upload/` module: schemas, repository, service, router
- [x] `schemas.py`: UploadRequest, UploadResult, ImportSummary
- [x] `repository.py`: Store imported data in `search_console_data` table
- [x] `service.py`: Parse CSV/JSON/ZIP, validate columns, normalize data, import
- [x] `router.py`: POST `/api/sc-upload/upload` endpoint
- [x] CSV parser: Handle Google Search Console export format
- [x] JSON parser: Handle GSC API response format
- [x] ZIP parser: Handle GSC "Performance on Search" ZIP export (Chart, Queries, Pages, Countries, Devices)
- [x] Column mapping: Auto-detect column names (Date, Query, Page, Clicks, etc.)
- [x] Data validation: Check required columns, data types, date formats
- [x] Deduplication: COALESCE-based upsert for rows with NULL device/country
- [x] Import summary: Return count of rows imported, skipped, errors, date range
- [x] Frontend: File upload UI on Search Console page (always visible)
- [ ] Drag & drop support for CSV/JSON/ZIP files
- [ ] Preview imported data before committing
- [ ] Progress indicator during import
- [ ] Error handling: Show validation errors with row numbers
- [x] **✅ Done when:** user can upload a CSV/JSON/ZIP file from Search Console export and see the data in analytics

### Supported File Formats

1. **CSV (Google Search Console export)**
   - Direct export from Performance report
   - Columns: Date, Query, Page, Clicks, Impressions, CTR, Position
   - Encoding: UTF-8

2. **JSON (API response format)**
   - Response from Search Console API
   - Structure: { rows: [{ keys: [...], clicks, impressions, ctr, position }] }

3. **ZIP (GSC "Performance on Search" export)**
   - Chart.csv: per-day performance rows
   - Queries.csv, Pages.csv, Countries.csv, Devices.csv: aggregated dimensions
   - CTR percentage strings normalized to ratios, commas stripped

4. **CSV (URL Inspection)**
   - Export from URL Inspection tool
   - Columns: URL, Coverage, Crawled as, Indexing, Last crawl

5. **CSV (Index Coverage)**
   - Export from Index Coverage report
   - Columns: Status, Category, Count, Examples

6. **CSV (Links Report)**
   - Export from Links report
   - Columns: Target page, Source page, Anchor text, First seen, Last seen

---

## Current next action

> All 34 phases complete. Consider improvements:
> - Drag & drop file upload support
> - Data preview before import
> - Row-level error reporting
> - Run `cargo tauri dev` (Rust toolchain required) for the packaged desktop app.
