# Changelog

All notable changes to SEO Content Intelligence are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [v1.17.0] — 2026-08-20

### Added
- Export button to download import history as CSV
- GET /api/sc-upload/export endpoint
- CSV includes all 13 import fields
- 1 new test for export endpoint

---

## [v1.16.0] — 2026-08-20

### Added
- Delete button for individual imports in history table
- Confirmation dialog before deletion
- DELETE /api/sc-upload/imports/{id} endpoint
- 2 new tests for delete functionality

---

## [v1.15.0] — 2026-08-20

### Added
- Import statistics summary with 3 KPI cards (Total Imports, Total Rows, Last Import)
- Parallel data fetching for imports and stats

---

## [v1.14.0] — 2026-08-20

### Added
- Import history table below upload section showing previous imports
- Columns: filename, type, status, rows imported, rows skipped, date
- Color-coded status indicators (completed/failed/processing)
- Auto-refresh after successful uploads
- Manual refresh button for import history

---

## [v1.13.0] — 2026-08-20

### Added
- Import type dropdown on Search Console page (Performance, URL Inspection, Index Coverage, Links)
- Descriptions for each import type in the dropdown

---

## [v1.12.0] — 2026-08-20

### Added
- URL Inspection import: coverage, crawled_as, crawl_allowed, page_fetch, indexing status
- Index Coverage import: status, category, count, affected URLs
- Links import: target/source pages, anchor text, first/last seen dates
- Auto-detect column names for all import types (CSV/JSON)
- 3 new database tables: sc_url_inspection, sc_coverage, sc_links
- 7 passing integration tests for all import types

---

## [v1.11.0] — 2026-08-20

### Added
- Search Console file upload: import SC data from CSV/JSON files
- Auto-detect column names from Google Search Console exports
- Import tracking with stats and history
- 4 API endpoints: upload, imports, import detail, stats
- File upload section on Search Console page
- 4 passing integration tests

---

## [v1.10.0] — 2026-08-20

### Added
- Backend integration tests with FastAPI TestClient (17 tests)
- Full API flow testing: Research → Idea → Plan content pipeline

---

## [v1.9.0] — 2026-08-20

### Added
- Tests for all 25 page components (21 new tests, 120 total)
- Direct API mocking for complex multi-useAsync pages
- Coverage improved: Statements 22.47%, Branches 22.46%, Lines 23.32%

---

## [v1.8.0] — 2026-08-20

### Added
- Page component tests for ABTesting, ArticlePlanner, Opportunities (24 new tests, 101 total)
- Coverage improved: Statements 8.15%, Branches 8.48%, Lines 8.18%

### Fixed
- Badge component now handles undefined/null values gracefully

---

## [v1.7.0] — 2026-08-20

### Added
- Page component tests for References, Ideas, Keywords, Research (16 new tests, 89 total)
- Coverage improved: Statements 6.42%, Branches 6.56%, Lines 6.41%

---

## [v1.6.0] — 2026-08-20

### Added
- Page component tests for Content, Audit, Dashboard (18 new tests, 73 total)
- Shared `renderWithProviders` test utility with router + store wrappers
- Coverage improved: Statements 4.48%, Branches 4.10%, Lines 4.56%

---

## [v1.5.0] — 2026-08-20

### Added
- API service layer tests (29 new tests, 55 total)
- `api.ts` tests: HTTP methods (GET/POST/PUT/PATCH/DELETE), error handling, token injection, Content-Type headers
- `desktop.ts` tests: deepLinkToRoute, isDesktop, bootstrapBackendToken no-ops
- `telemetry.ts` tests: track, installCrashReporter, error event handling, crash reporting

---

## [v1.4.0] — 2026-08-20

### Added
- Vitest coverage reporting with `@vitest/coverage-v8` provider
- Text, text-summary, and LCOV reporters
- `npm run test:coverage` script
- Coverage thresholds and exclusions configured in `vite.config.ts`

---

## [v1.3.0] — 2026-08-20

### Added
- Frontend unit testing with Vitest + Testing Library + jsdom
- 26 unit tests across 3 test files
- ThemeStore tests: theme toggle, localStorage persistence, data-theme attribute
- Common component tests: Loading, ErrorBox, Empty, Badge, AiBadge
- Hook tests: useAsync (loading, data, error, reload, deps change)
- `npm test` and `npm run test:watch` scripts

---

## [v1.2.0] — 2026-08-20

### Added
- Dark/Light theme toggle with CSS variable theming
- Light theme: clean white (`#f5f6f8`) background
- Theme toggle button in sidebar (☀️/🌙)
- Preference persisted in `localStorage` under `sci-theme` key
- Smooth 0.2s CSS transitions between themes

### Changed
- CSS variables refactored to support both themes via `data-theme` attribute on `<html>`

---

## [v1.1.0] — 2026-08-20

### Added
- Code splitting with `React.lazy()` for all 31 page components
- Each page loads as its own chunk on demand
- `Suspense` boundary with loading fallback (⏳)

### Performance
- Initial JS bundle: 420 KB → 192 KB (**-54%**)
- Gzipped initial load: 105 KB → 62 KB (**-41%**)
- 32 total chunks (1 core + 31 page chunks)

---

## [v1.0.0] — 2026-08-20

### Complete — All 30 Phases

First stable release of SEO Content Intelligence.

#### Features

| Phase | Feature |
|-------|---------|
| 0 | Architecture: 33-table schema, FastAPI skeleton, DI pattern |
| 1 | Desktop foundation: Tauri shell, React+TS frontend, SQLite backend |
| 2 | Website connection: Crawler, platform detectors, sitemap parser |
| 3 | Search Console: OAuth, property discovery, historical + incremental import |
| 4 | SEO engine: Analyzer, scoring, technical/content/links/metadata, rule references |
| 5 | Recommendation engine: 9-field recommendations with What·Why·Evidence·Confidence·Action |
| 6 | Content audit: Verdicts (Keep·Improve·Refresh·Consolidate·Review) |
| 7 | Content Ideas: YouTube/Podcast/SC/News inputs, research + content gap analysis |
| 8 | Discussion: AI provider abstraction, chat + decision log |
| 9 | Article Planner: Outline, evidence, intent, audience, internal links |
| 10 | AI drafting: Generated drafts, SEO check, fact-check, human approval gate |
| 11 | Advanced integrations: WordPress/GitHub publishing, GA, topic clusters, internal links |
| 12 | Desktop hardening: Auto-updates, deep linking, keychain, proxy, crash reporting |
| 13 | Bulk operations: Bulk crawl/analyze/ideas with background job tracking |
| 14 | Monitoring & Alerts: 5 checkers, 3 alerters (email/Slack/desktop), 15 endpoints |
| 15 | A/B Testing: Z-test measurement, 95% confidence, variant comparison |
| 16 | Competitor Analysis: Gap engine (new/improve/quick-win), rankings, competitor import |
| 17 | Analytics Dashboard: CSS-only charts, KPIs, period comparison, traffic/ranking data |
| 18 | Keyword Clustering: Jaccard similarity engine, auto-clustering from SC data |
| 19 | Schema Markup Builder: Article/FAQPage/HowTo/Product/BreadcrumbList/Organization generators |
| 20 | Content Calendar: Monthly grid + Kanban, pipeline management, deadlines |
| 21 | Backlink Monitor: Change tracking (gained/lost), profile analysis, CSV import |
| 22 | Page Speed Insights: SVG gauges, CWV thresholds (LCP/FID/CLS/FCP/TTFB) |
| 23 | Content Rewriter: Type-specific prompts, copy/select/apply, rewrite history |
| 24 | SEO Checklist: Auto-generate from findings + 13 standard items, 6 categories |
| 25 | Sitemap Generator: Configurable settings, URL overrides, valid XML output |
| 26 | Report Generator: Data collection + HTML rendering + PDF export |
| 27 | SERP Preview: Google-style card, live editor, real-time preview, tips |
| 28 | Redirect Manager: CRUD + bulk import (CSV), chain detection, check history |
| 29 | AI Content Brief Generator: SERP analysis, competitor insights, outline + FAQ generation |
| 30 | Content Refresh Scheduler: Staleness detection, trend analysis, priority scoring, refresh queue |

#### Stack
- **Desktop:** Tauri (Rust shell) with auto-updates, `sci://` deep linking, OS keychain
- **Frontend:** React 18 + TypeScript + Vite (code-split, dark/light theme)
- **Backend:** Python FastAPI + SQLite (60+ tables, 200+ API endpoints)
- **CI/CD:** GitHub Actions (Python 3.11/3.12 + Node 20)

#### Project Stats
- 35 backend modules, 8 engines, 12 integrations
- 31 frontend pages (code-split)
- 60+ database tables across 14 extension schemas
- 55 unit tests (6 test files)
