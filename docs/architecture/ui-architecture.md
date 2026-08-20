# UI Architecture v1

> React + TypeScript SPA rendered inside a Tauri window. Talks to the local
> FastAPI backend (see `api-architecture.md`). Layout: fixed left sidebar +
> scrollable content area (§21 of plan).

---

## Tech Choices

| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | React 18 + TypeScript | Plan requirement |
| Bundler | Vite | Fast dev server, Tauri-friendly static build |
| Routing | React Router v6 | Standard for SPA |
| Server state | TanStack Query | Caching, background refetch for sync jobs |
| Client state | Zustand | Lightweight stores (`stores/`) |
| Forms | React Hook Form + Zod | Typed validation |
| Charts | Recharts | SC trends, opportunity charts |
| Tables | TanStack Table | Sortable/filterable data grids |
| Styling | CSS Modules + design tokens | No heavy UI framework dependency |

---

## Navigation — Left Sidebar

```text
┌─────────────────────────────┐
│ SEO Intelligence            │
├─────────────────────────────┤
│ 🏠 Dashboard        /       │
│ 🌐 Websites         /websites
│ 📊 Search Console   /search-console
│ 📄 Content          /content│
│ 🔑 Keywords         /keywords
│ 🎯 Opportunities    /opportunities
│ 🔍 Content Audit    /audit  │
│ 💡 Content Ideas    /ideas  │
│ 🔬 Research         /research
│ 📝 Article Planner  /article-planner
│ 📚 References       /references
│ 📈 Reports          /reports│
│                     --------│
│ ⚙ Settings          /settings
└─────────────────────────────┘
```

Discussion lives inside Research (`/research/discussion/:id`).

---

## Pages (14)

| Page | Route | Primary data | Key interactions |
|------|-------|--------------|------------------|
| Dashboard | `/` | Health, sync summary, top findings | KPI cards, recent activity |
| Websites | `/websites` | `websites` | Add/edit/delete, detect, test, crawl status |
| Search Console | `/search-console` | `search_console_*` | Connect (OAuth), sync, query/page tables, period compare |
| Content | `/content` | `pages` + `page_content` | Page list, detail with headings/images/links |
| Keywords | `/keywords` | `keywords` + SC metrics | Group, intent tags |
| Opportunities | `/opportunities` | `seo_findings` | Filter by confidence/severity/type, accept/dismiss |
| Content Audit | `/audit` | `pages` + verdicts | Verdict board: Keep · Improve · Refresh · Consolidate · Review |
| Content Ideas | `/ideas` | `content_ideas` + `research_sources` | Add source (YouTube/Podcast/URL/Manual), scores, availability badges |
| Research | `/research` | `research_*` | Topics/claims/questions views, discussion threads, decisions |
| Article Planner | `/article-planner` | `article_plans` | Brief editor, outline, prompt, fact-check list |
| References | `/references` | `reference_docs` + `seo_rules` | Category browser, rule ↔ reference links |
| Reports | `/reports` | aggregated | Generate/export |
| Settings | `/settings` | `settings`, `ai_providers`, connections | Sectioned per plan §22 |

Each page = `pages/<Name>/index.tsx` (layout) + feature components from `features/<domain>/`.

---

## Folder Responsibilities

```text
src/
├── app/          # Router, providers, app shell composition
├── layouts/      # AppShell (sidebar + header + outlet)
├── pages/        # One folder per route — composition only, no business logic
├── features/     # Domain widgets (dashboard/, search-console/, seo/...)
├── components/   # Reusable UI: charts/ tables/ dialogs/ forms/ cards/ common/
├── services/     # Typed API client (one file per backend prefix)
├── hooks/        # useWebsites(), useFindings()... — TanStack Query wrappers
├── stores/       # Zustand UI state (active website, sidebar state)
├── types/        # Shared TS types mirroring backend schemas (snake_case)
└── utils/        # Formatting, dates, URLs
```

**Rules:** pages never call `fetch` directly (go through hooks → services); `types/` mirrors backend Pydantic schemas; availability states always render an explicit badge (Rule: never pretend content was analyzed).

---

## Cross-Cutting Conventions

- **Pagination:** every list uses `{ items, total, page, page_size }` from the API; shared `<DataTable>` handles it.
- **Error envelope:** single interceptor maps `{ error: { code, message } }` to toasts; `404` → empty-state.
- **Long jobs:** crawl/sync/extract start → poll `status` endpoint → toast on completion.
- **Recommendation cards:** always render What · Why · Evidence · Source · Confidence; `ai_suggestion` type shows an explicit "AI suggestion" badge.
- **Active website:** global Zustand store; pages that need a website read it from the store, not the URL.
