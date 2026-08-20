# SEO Content Intelligence — Project Plan

> A Windows desktop application for SEO content intelligence, combining Search Console data,
> website crawling, research extraction, and AI-assisted content planning.

**Stack:** Tauri + React / TypeScript + Python + SQLite

---

## Table of Contents

| # | Section |
|----|---------|
| 1 | [Overall Architecture](#1-overall-architecture) |
| 2 | [Complete Project Structure](#2-complete-project-structure) |
| 3 | [Backend Modules](#3-backend-modules) |
| 4 | [Website Module](#4-website-module) |
| 5 | [Search Console Module](#5-search-console-module) |
| 6 | [Website Crawler](#6-website-crawler) |
| 7 | [WordPress Integration](#7-wordpress-integration) |
| 8 | [Astro Integration](#8-astro-integration) |
| 9 | [YouTube Module](#9-youtube-module) |
| 10 | [Podcast Module](#10-podcast-module) |
| 11 | [Research Engine](#11-research-engine) |
| 12 | [AI Provider Layer](#12-ai-provider-layer) |
| 13 | [SEO Analysis Engine](#13-seo-analysis-engine) |
| 14 | [Reference System](#14-reference-system) |
| 15 | [SEO Rules](#15-seo-rules) |
| 16 | [SEO Recommendation Object](#16-seo-recommendation-object) |
| 17 | [Content Ideas Module](#17-content-ideas-module) |
| 18 | [Article Planner](#18-article-planner) |
| 19 | [Database](#19-database) |
| 20 | [Frontend Structure](#20-frontend-structure) |
| 21 | [UI Navigation](#21-ui-navigation) |
| 22 | [Settings](#22-settings) |
| 23 | [Development Skills Required](#23-development-skills-required) |
| 24 | [Development Phases](#24-development-phases) |
| 25 | [Development Rules](#25-development-rules) |
| 26 | [First Folder Creation](#26-first-folder-creation) |
| 27 | [The Very Next Task](#27-the-very-next-task) |

---

## 1. Overall Architecture

The project is organized into nine top-level areas:

```text
seo_content_intelligence/
├── desktop/      # Tauri shell (Windows packaging, secure storage)
├── backend/      # Python FastAPI application logic
├── frontend/     # React + TypeScript UI
├── database/     # Schema, migrations, seeds
├── docs/         # Architecture, SEO, product documentation
├── scripts/      # Setup, import, maintenance utilities
├── tests/        # Unit and integration tests
├── data/         # Raw/processed data, cache, exports, backups
└── config/       # Environment-specific configuration
```

---

## 2. Complete Project Structure

```text
seo_content_intelligence/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── package.json
│
├── desktop/
│   ├── src-tauri/
│   │   ├── src/
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json
│   └── icons/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── utils/
│   │   └── assets/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config, security, logging, exceptions
│   │   ├── api/           # routes, dependencies
│   │   ├── database/      # connection, models, migrations
│   │   ├── modules/       # business modules (see §3)
│   │   ├── integrations/  # external systems (see §6–§10)
│   │   ├── engines/       # analysis engines (see §13)
│   │   ├── services/
│   │   └── utils/
│   └── tests/
│
├── database/
│   ├── schema/
│   ├── migrations/
│   └── seeds/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── cache/
│   ├── exports/
│   └── backups/
│
├── docs/
│   ├── architecture/
│   ├── database/
│   ├── seo/
│   ├── integrations/
│   ├── product/
│   └── development/
│
├── scripts/
│   ├── setup/
│   ├── database/
│   ├── import/
│   └── maintenance/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── sample_data/
│
└── config/
    ├── development/
    └── production/
```

---

## 3. Backend Modules

> **This is the most important part.** Each module must be independent.

Location: `backend/app/modules/`

| Module | Purpose |
|--------|---------|
| `websites/` | Website registry, platform detection |
| `search_console/` | Google Search Console data |
| `pages/` | Crawled page inventory |
| `content/` | Content inventory and status |
| `keywords/` | Keyword tracking and grouping |
| `seo_analysis/` | SEO analysis orchestration |
| `seo_opportunities/` | Opportunity detection |
| `content_audit/` | Keep / improve / refresh decisions |
| `content_ideas/` | Idea generation and validation |
| `research/` | Source research extraction |
| `discussion/` | AI research discussion |
| `article_planner/` | Briefs, outlines, prompts |
| `references/` | Official reference registry |
| `topic_clusters/` | Cluster and pillar mapping |
| `internal_links/` | Internal linking analysis |
| `reports/` | Report generation |
| `settings/` | Application settings |

---

## 4. Website Module

```text
websites/
├── models.py
├── schemas.py
├── service.py
├── repository.py
├── router.py
└── detectors.py
```

**Responsibilities:**

- Add / edit / delete website
- Detect WordPress
- Detect Astro / static sites
- Detect sitemap
- Test website connectivity
- Manage website configuration

---

## 5. Search Console Module

```text
search_console/
├── models.py
├── schemas.py
├── service.py
├── repository.py
├── router.py
├── oauth.py
├── api_client.py
├── importer.py
├── normalizer.py
└── analytics.py
```

**Responsibilities:**

| Capability | Description |
|------------|-------------|
| Google OAuth | Authenticate with Google account |
| Property discovery | List Search Console properties |
| Connect property | Bind a property to a website |
| Download data | Fetch query/page performance data |
| Historical import | One-time backfill of past data |
| Incremental import | Daily delta sync |
| Store data | Persist raw + normalized data |
| Compare periods | Period-over-period analytics |

---

## 6. Website Crawler

> The crawler is a **separate integration**, not a module.

Location: `backend/app/integrations/`

```text
integrations/
├── wordpress/
├── sitemap/
├── crawler/
├── github/
├── youtube/
├── podcast/
└── google/
```

### Crawler internals

```text
crawler/
├── crawler.py
├── parser.py
├── html_extractor.py
├── metadata.py
├── links.py
├── schema_parser.py
└── robots.py
```

### What it extracts

| Field | Field |
|-------|-------|
| Title | Canonical |
| Meta description | Schema |
| Headings | Published date |
| Content | Modified date |
| Links | Images |
| ALT text | — |

---

## 7. WordPress Integration

```text
wordpress/
├── client.py
├── auth.py
├── posts.py
├── pages.py
├── categories.py
├── media.py
└── mapper.py
```

**Capabilities — phased:**

| Phase | Capability |
|-------|------------|
| Initially | **READ ONLY** |
| Later | Read post · Update post · Create draft · Publish |

---

## 8. Astro Integration

**Initially:** `sitemap/` + `crawler/`

**Later:** `github/` — GitHub integration can access:

- `.md` files
- `.mdx` files
- Astro content collections

**Eventually (future):**

```text
Idea → Article → Markdown → Git commit → Astro build
```

> This is later — not part of the initial build.

---

## 9. YouTube Module

```text
youtube/
├── client.py
├── metadata.py
├── transcript.py
├── extractor.py
├── analyzer.py
└── models.py
```

**It should handle:**

- URL, video ID, title, description
- Channel, published date
- Transcript (where available)
- Chapters (where available)
- Extraction status and errors

**Availability states — must be recorded explicitly:**

| State | Meaning |
|-------|---------|
| ✅ Transcript available | Full analysis possible |
| ⚠️ Transcript unavailable | Limited analysis |
| ℹ️ Metadata only | Title/description analysis only |

> **Never pretend we analyzed unavailable content.**

---

## 10. Podcast Module

```text
podcast/
├── detector.py
├── metadata.py
├── transcript.py
├── extractor.py
└── analyzer.py
```

**Possible sources:** episode page · show notes · transcript · RSS feed

> Again, availability must be clearly recorded.

---

## 11. Research Engine

> A major module. It converts raw sources into structured research.

```text
research/
├── models.py
├── schemas.py
├── service.py
├── source_analyzer.py
├── topic_extractor.py
├── claim_extractor.py
├── question_extractor.py
├── content_gap.py
└── evidence.py
```

**Input → Output:**

```text
YouTube · Podcast · Article · News · Manual idea
                    │
                    ▼
         Structured Research
   (topics, claims, questions, gaps, evidence)
```

---

## 12. AI Provider Layer

```text
integrations/ai/
├── base.py
├── openai.py
├── gemini.py
├── anthropic.py
├── models.py
├── prompt_builder.py
└── provider_manager.py
```

**Architecture:**

```text
         AIProvider
             │
   ┌─────────┼──────────┐
   ▼         ▼          ▼
 OpenAI   Gemini   Anthropic
```

> The rest of the application doesn't care which provider is being used.

---

## 13. SEO Analysis Engine

Location: `backend/app/engines/`

```text
engines/
├── seo/
│   ├── analyzer.py
│   ├── rules_engine.py
│   ├── scoring.py
│   ├── technical.py
│   ├── content.py
│   ├── links.py
│   ├── metadata.py
│   └── structured_data.py
│
├── search_console/
│   ├── opportunity_engine.py
│   ├── ranking_engine.py
│   ├── ctr_engine.py
│   └── cannibalization.py
│
└── content/
    ├── gap_engine.py
    ├── topic_engine.py
    └── recommendation_engine.py
```

---

## 14. Reference System

> This should be a **first-class module**.

```text
references/
├── models.py
├── schemas.py
├── service.py
├── repository.py
├── source_registry.py
├── document_registry.py
├── verification.py
└── categories.py
```

**Categories:**

| Category | Category |
|----------|----------|
| Google SEO | SEBI |
| Google Search Console | AMFI |
| Google Structured Data | RBI |
| Google Spam Policies | Income Tax |
| AMC | Other Official |

---

## 15. SEO Rules

> **Don't mix rules with references.**

```text
seo_rules/
├── models.py
├── registry.py
├── evaluator.py
├── severity.py
├── technical_rules.py
├── content_rules.py
└── financial_rules.py
```

**Relationship:**

```text
Rule → Reference → Official document
```

---

## 16. SEO Recommendation Object

> **This is critical.** Every recommendation must be explainable.

**Required fields:**

| Field | Purpose |
|-------|---------|
| Recommendation | What to do |
| Why | Reasoning |
| Evidence | Supporting data |
| Data | Raw numbers |
| Rule | Rule that triggered it |
| Reference | Official source |
| Confidence | High / Medium / Low |
| Severity | Impact level |
| Suggested Action | Concrete next step |

**Example:**

| Field | Value |
|-------|-------|
| **Recommendation** | Improve Article |
| **Why** | High impressions with ranking opportunity |
| **Evidence** | 18,500 impressions · Position 6.4 · CTR 1.51% |
| **Source** | Search Console |
| **Type** | Data-based recommendation |
| **Confidence** | High |

---

## 17. Content Ideas Module

```text
content_ideas/
├── models.py
├── schemas.py
├── service.py
├── scoring.py
├── idea_generator.py
├── idea_validator.py
└── workflow.py
```

**Inputs:** YouTube · Podcast · Search Console · Website · News · Manual

> It generates **potential ideas, not automatic articles**.

---

## 18. Article Planner

```text
article_planner/
├── models.py
├── schemas.py
├── service.py
├── outline.py
├── seo_brief.py
├── prompt_generator.py
├── fact_check.py
└── finalizer.py
```

**Final output contains:**

| Output | Output |
|--------|--------|
| Title | Internal links |
| Primary topic | Sources |
| Search intent | Facts to verify |
| Audience | Search Console evidence |
| Outline | Source inspiration |
| Questions | Things to avoid |

---

## 19. Database

> **SQLite initially.** Don't create all tables immediately — we'll create them in stages.

### Main tables

| Group | Tables |
|-------|--------|
| **Websites** | `websites`, `website_connections` |
| **Search Console** | `search_console_properties`, `search_console_data` |
| **Pages** | `pages`, `page_content`, `page_links` |
| **Keywords** | `keywords` |
| **Ideas & Research** | `content_ideas`, `research_sources`, `research_topics`, `research_claims`, `research_questions` |
| **Discussion** | `discussions`, `discussion_messages`, `discussion_decisions` |
| **Planning** | `article_plans` |
| **SEO** | `seo_rules`, `references`, `seo_findings`, `seo_actions` |
| **Structure** | `topic_clusters`, `internal_links` |
| **System** | `ai_providers`, `settings`, `sync_logs` |

---

## 20. Frontend Structure

```text
frontend/src/
├── app/
│
├── pages/
│   ├── Dashboard/
│   ├── Websites/
│   ├── SearchConsole/
│   ├── Content/
│   ├── Keywords/
│   ├── Opportunities/
│   ├── Audit/
│   ├── Ideas/
│   ├── Research/
│   ├── Discussion/
│   ├── ArticlePlanner/
│   ├── References/
│   ├── Reports/
│   └── Settings/
│
├── features/
│   ├── dashboard/
│   ├── search-console/
│   ├── content/
│   ├── research/
│   ├── discussion/
│   └── seo/
│
├── components/
│   ├── charts/
│   ├── tables/
│   ├── dialogs/
│   ├── forms/
│   ├── cards/
│   └── common/
│
├── services/
├── hooks/
├── stores/
├── types/
└── utils/
```

---

## 21. UI Navigation

Recommended layout: **left sidebar**.

```text
┌─────────────────────────────┐
│ SEO Intelligence             │
├─────────────────────────────┤
│ 🏠 Dashboard                 │
│ 🌐 Websites                  │
│ 📊 Search Console            │
│ 📄 Content                   │
│ 🔑 Keywords                  │
│ 🎯 Opportunities             │
│ 🔍 Content Audit             │
│ 💡 Content Ideas             │
│ 🔬 Research & Discussion     │
│ 📝 Article Planner           │
│ 📚 References                │
│ 📈 Reports                   │
│                             │
│ ⚙ Settings                  │
└─────────────────────────────┘
```

---

## 22. Settings

```text
Settings
├── General
├── Websites
├── Google
│   └── Search Console
├── AI Providers
│   ├── OpenAI
│   ├── Gemini
│   └── Anthropic
├── WordPress
├── GitHub
├── Crawler
├── References
├── SEO Rules
├── Data
├── Backup
└── Security
```

---

## 23. Development Skills Required

| Area | Skills |
|------|--------|
| **Python** | FastAPI · Pydantic · SQLAlchemy · Pandas (where useful) · HTTP clients · HTML parsing · Async programming |
| **TypeScript / Frontend** | React · React Router · state management · forms · charts · tables · API integration |
| **Tauri / Desktop** | Rust basics · Tauri commands · Windows packaging · secure storage |
| **SQLite** | SQL · schema design · migrations · indexing · relationships |
| **APIs** | Google OAuth · Search Console API · WordPress REST API · YouTube data retrieval · AI APIs · GitHub API (later) |
| **SEO** | Crawling · indexing · sitemap · robots.txt · canonical · structured data · metadata · internal links · Search Console · search intent · content quality · technical SEO |
| **AI** | API integration · prompt engineering · structured output · conversation context · source/evidence handling · hallucination control |
| **Security** | OAuth · API key storage · encryption/credential storage · secrets management · local database security |

---

## 24. Development Phases

> **Don't try to build the whole thing in one go.**

| Phase | Name | Deliverable |
|-------|------|-------------|
| 0 | Architecture | Requirements, folder structure, database design, API & UI architecture |
| 1 | Desktop foundation | Tauri + React + Python + SQLite — app opens successfully |
| 2 | Website connection | Add website → detect → sitemap → crawl → see pages |
| 3 | Search Console | OAuth → property selection → historical import → incremental sync |
| 4 | SEO engine | Page analysis, technical SEO, metadata, links, structured data, SC analysis |
| 5 | Recommendation engine | Why + Evidence + Recommendation + Confidence + Reference + Action |
| 6 | Content audit | Keep · Improve · Refresh · Consolidate · Review |
| 7 | Content Ideas | YouTube · Podcast · URL · Manual idea → extraction/research |
| 8 | Discussion | Interactive research assistant |
| 9 | Article Planner | SEO brief → outline → sources → internal links → prompt |
| 10 | AI drafting | Generate draft → edit → fact check → SEO check → human approval |
| 11 | Advanced integrations | WordPress/GitHub publishing, Analytics, clusters, reports |

### Phase details

**Phase 0 — Architecture** ✅ Requirements · Folder structure · Database design · API architecture · UI architecture

**Phase 1 — Desktop foundation**
Build: `Tauri + React + Python + SQLite` → get the application opening successfully.

**Phase 2 — Website connection**
Implement: Add Website · Detect website · Sitemap · Crawler · Page database.
**At the end:** Add website → crawl → see pages.

**Phase 3 — Search Console**
Implement: Google OAuth · Property selection · Historical import · Incremental sync · Search data.
**At the end:** Website + Search Console are connected.

**Phase 4 — SEO engine**
Implement: Page analysis · Technical SEO · Metadata · Links · Structured data · Search Console analysis.

**Phase 5 — Recommendation engine** ⭐ *One of the most important milestones.*
Build: Why · Evidence · Recommendation · Confidence · Reference · Action.

**Phase 6 — Content audit**
Build: Keep · Improve · Refresh · Consolidate · Review.

**Phase 7 — Content Ideas**
Inputs: YouTube · Podcast · URL · Manual idea → then extraction/research.

**Phase 8 — Discussion**

```text
Research → AI → You → AI → Decision
```

This becomes your interactive research assistant.

**Phase 9 — Article Planner** (only after Discussion)

```text
Final idea → SEO brief → Outline → Sources → Internal links → Prompt
```

**Phase 10 — AI drafting**
Generate Draft → Edit → Fact check → SEO check → Human approval.

**Phase 11 — Advanced integrations** (later)
WordPress publishing · GitHub/Astro publishing · Google Analytics · Topic clusters · Internal linking · Automated reports.

---

## 25. Development Rules

> Because previous projects developed duplicate modules, enforce these from the beginning.

### Rule 1 — One responsibility per module

Don't create `portfolio.py`, `portfolio_engine.py`, `portfolio_service.py`, `portfolio_manager.py` unless each has a clearly different responsibility.

### Rule 2 — No duplicate engines

`seo_analysis/` should be the single owner of SEO analysis.

### Rule 3 — API integration ≠ business logic

Keep **Google API** separate from **SEO analysis**.

### Rule 4 — Database ≠ analysis

Don't put calculations into database models.

### Rule 5 — AI ≠ truth

AI recommendations must be marked as **AI suggestion** unless supported by actual data/rules.

### Rule 6 — Every recommendation needs an explanation

What? · Why? · Evidence? · Source? · Action?

### Rule 7 — Keep raw data

Never overwrite the original Search Console import:

```text
raw → normalized → analysis
```

This allows us to recalculate later.

---

## 26. First Folder Creation

> For now, **don't create hundreds of files.** Create the project root and these folders first:

**Step 1 — Project root:**

```text
seo_content_intelligence/
├── backend/
├── frontend/
├── desktop/
├── database/
├── data/
├── docs/
├── scripts/
├── tests/
└── config/
```

**Step 2 — Inside backend:**

```text
backend/
└── app/
    ├── core/
    ├── api/
    ├── database/
    ├── modules/
    ├── integrations/
    ├── engines/
    ├── services/
    └── utils/
```

**Step 3 — Modules:**

```text
modules/
├── websites/
├── search_console/
├── pages/
├── content/
├── keywords/
├── seo_analysis/
├── seo_opportunities/
├── content_audit/
├── content_ideas/
├── research/
├── discussion/
├── article_planner/
├── references/
└── settings/
```

> **Stop there initially.** Don't start filling every folder with code.

---

## 27. The Very Next Task

After creating the folder structure, the next step is **Database Design v1** — defining every table and field.

**Example — `websites`:**

| Column |
|--------|
| `id` |
| `name` |
| `url` |
| `platform` |
| `sitemap_url` |
| `status` |
| `created_at` |
| `updated_at` |

**Example — `search_console_data`:**

| Column |
|--------|
| `id` |
| `website_id` |
| `date` |
| `query` |
| `page_url` |
| `clicks` |
| `impressions` |
| `ctr` |
| `position` |
| `created_at` |

**Then relationships between:**

```text
Website → Pages → Search Console → Keywords → Recommendations
       → Content Ideas → Discussion → Article Plan → References
```

> Once the database is correct, we can start coding the actual application with a much
> lower risk of the duplicate-module/database problems encountered before.
