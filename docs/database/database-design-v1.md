# Database Design v1

> SQLite schema for SEO Content Intelligence. Schema file: [`database/schema/schema_v1.sql`](../../database/schema/schema_v1.sql)
> Tables are created **in stages** per development phase — this document defines the full target design.

---

## Design Principles

| # | Principle | How it's enforced |
|---|-----------|-------------------|
| 1 | Raw data is never overwritten | `search_console_raw` + `sync_logs.raw_file_path` keep untouched payloads (`raw → normalized → analysis`) |
| 2 | Database ≠ analysis | Tables store facts only; engines in `backend/app/engines/` compute findings |
| 3 | Every recommendation is explainable | `seo_findings` carries `why`, `evidence`, `data`, `confidence`, linked `rule_id` + `reference_id` |
| 4 | AI ≠ truth | `seo_findings.rec_type` distinguishes `data_based` / `rule_based` / `ai_suggestion` |
| 5 | Availability is recorded, never faked | `research_sources.availability_status`: `full` / `transcript_unavailable` / `metadata_only` |

---

## Tables by Group

| Group | Tables | Phase |
|-------|--------|-------|
| **Websites** | `websites`, `website_connections` | 2 |
| **Search Console** | `search_console_properties`, `search_console_data`, `search_console_raw` | 3 |
| **Pages** | `pages`, `page_content`, `page_links` | 2 |
| **Keywords** | `keywords` | 3–4 |
| **Research & Ideas** | `research_sources`, `research_topics`, `research_claims`, `research_questions`, `content_ideas` | 7 |
| **Discussion** | `discussions`, `discussion_messages`, `discussion_decisions` | 8 |
| **Planning** | `article_plans` | 9 |
| **SEO** | `reference_docs`, `seo_rules`, `seo_findings`, `seo_actions` | 4–5 |
| **Structure** | `topic_clusters`, `topic_cluster_pages`, `internal_links` | 11 |
| **System** | `ai_providers`, `settings`, `sync_logs` | 1, 8 |

---

## Relationship Chain

The core entity flow follows the plan:

```text
Website → Pages → Search Console → Keywords → Recommendations
       → Content Ideas → Discussion → Article Plan → References
```

Mapped to foreign keys:

```text
websites
 ├── website_connections.website_id
 ├── pages.website_id ───────────────┐
 │    ├── page_content.page_id       │
 │    ├── page_links.page_id         │
 │    └── page_links.target_page_id  │
 ├── search_console_properties.website_id
 │    └── search_console_data.property_id / .website_id
 │         └── search_console_raw.property_id
 ├── keywords.website_id             │   (keywords.normalized ↔ search_console_data.query)
 ├── seo_findings.website_id ────────┘
 │    ├── seo_findings.page_id → pages
 │    ├── seo_findings.rule_id → seo_rules ── reference_id → reference_docs
 │    └── seo_actions.finding_id
 ├── content_ideas.website_id
 │    └── discussions.idea_id
 │         ├── discussion_messages.discussion_id
 │         └── discussion_decisions.discussion_id
 ├── article_plans.website_id
 │    ├── .idea_id → content_ideas
 │    └── .discussion_id → discussions
 └── topic_clusters.website_id
      ├── .pillar_page_id → pages
      └── topic_cluster_pages {cluster_id, page_id}
```

---

## Key Design Decisions

### 1. `search_console_data` — normalized metrics

- Unique constraint on `(property_id, date, query, page_url, device, country)` so incremental imports **upsert** instead of duplicating rows.
- Original API responses are preserved separately in `search_console_raw` (JSON payload + request dimensions) and on disk via `sync_logs.raw_file_path` → re-importable anytime.

### 2. `pages` vs `page_content` split

Heavy payloads (full text, headings, images, schema JSON) live 1:1 in `page_content`, keeping `pages` light for list views and joins.

### 3. `page_links` (crawled) vs `internal_links` (recommended)

- `page_links` = facts extracted by the crawler.
- `internal_links` = suggestions produced by engines, with lifecycle `suggested → applied / dismissed`.

### 4. `seo_findings` is the Recommendation object (§16 of plan)

| Recommendation field | Column |
|----------------------|--------|
| Recommendation | `recommendation` |
| Why | `why` |
| Evidence | `evidence` |
| Data | `data` (JSON) |
| Rule | `rule_id` → `seo_rules` |
| Reference | `reference_id` → `reference_docs` |
| Confidence | `confidence` |
| Severity | `severity` |
| Suggested Action | `seo_actions` (one per finding) |

### 5. `Rule → Reference → Official document`

`seo_rules.reference_id` links every rule to an official `reference_docs` row (Google SEO, SEBI, AMFI, RBI, Income Tax, AMC...). Rules and references stay in separate tables — never mixed.

> Table is named `reference_docs` because `references` is a reserved SQL keyword.

### 6. Security

`ai_providers.api_key_encrypted` stores only encrypted material; plaintext keys are never persisted (handled by Tauri secure storage at runtime).

---

## Conventions

- **PK:** `id INTEGER PRIMARY KEY AUTOINCREMENT` everywhere.
- **Timestamps:** `created_at` / `updated_at` as ISO text (`datetime('now')`); application layer maintains `updated_at`.
- **JSON columns:** stored as `TEXT` containing valid JSON; parsed by Pydantic schemas, never queried by SQL logic (Rule 4).
- **Enums:** stored as lowercase strings, validated by Pydantic — SQLite-friendly and migration-safe.
- **FKs:** `PRAGMA foreign_keys = ON` enforced at connection time (`backend/app/database/connection.py`).
- **Naming:** snake_case tables/columns; indexes prefixed `idx_<table>_<columns>`.

---

## Migration Notes

- Schema v1 ships as a single DDL file; split into numbered migrations (`database/migrations/0001_initial.sql`, ...) once Phase 1 wires up the migration runner.
- Staged creation order mirrors the phases: Phase 1 creates system tables only; each phase adds its own group.
