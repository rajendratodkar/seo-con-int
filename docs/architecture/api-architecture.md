# API Architecture v1

> FastAPI backend for SEO Content Intelligence. Runs as a **local sidecar process**
> managed by Tauri — never exposed to the network. Frontend talks to it over
> `http://127.0.0.1:<port>` (port written to a runtime file; token-guarded).

---

## Layering Rules

Every business module follows one internal shape (Rule 1 — one responsibility per file):

```text
router.py      → HTTP layer only: parse request, call service, return schema
service.py     → Business logic and orchestration (no SQL, no HTTP objects)
repository.py  → Data access only (SQLAlchemy queries, no business decisions)
models.py      → SQLAlchemy ORM models (no calculations — Rule 4)
schemas.py     → Pydantic request/response schemas (API contract)
```

**Dependency direction (strict, one-way):**

```text
router → service → repository → models
            │
            └──→ integrations/ (API clients) · engines/ (analysis)
```

- Modules never import each other's repositories — cross-module access goes through the other module's **service**.
- `integrations/` hold API clients only (Rule 3 — Google API ≠ SEO analysis).
- `engines/` are pure computation: take data in, return findings; no DB writes of their own.

---

## App Skeleton

```python
# backend/app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.api.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="SEO Content Intelligence",
        version=settings.app_version,
        lifespan=app_lifespan,          # DB init + staged migrations on startup
    )
    setup_logging(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api")
    return app

app = create_app()
```

```python
# backend/app/api/router.py
from fastapi import APIRouter
from app.modules.websites.router import router as websites_router
# ... one import per module, aggregated here ONLY

api_router = APIRouter()
api_router.include_router(health_router,    prefix="/health",       tags=["health"])
api_router.include_router(websites_router,  prefix="/websites",     tags=["websites"])
api_router.include_router(sc_router,        prefix="/search-console", tags=["search-console"])
# ... (full table below)
```

> The aggregator imports routers only. No business logic lives in `api/`.

---

## Route Map

All routes live under `/api`. Kebab-case prefixes, plural resources, REST verbs.

| Prefix | Module | Key endpoints (Phase 2+ shape) |
|--------|--------|--------------------------------|
| `/api/health` | core | `GET /` — liveness for Tauri |
| `/api/websites` | `websites/` | `GET · POST /`, `GET · PATCH · DELETE /{id}`, `POST /{id}/test`, `POST /{id}/detect` |
| `/api/websites/{id}/crawl` | `integrations/crawler` | `POST /start`, `GET /status` |
| `/api/search-console` | `search_console/` | `GET /oauth/url`, `POST /oauth/callback`, `GET /properties`, `POST /properties/{id}/connect`, `POST /sync` (historical/incremental), `GET /queries`, `GET /pages`, `GET /compare` |
| `/api/google-analytics` | `google_analytics/` | `GET /properties`, `POST /connect`, `GET · DELETE /connection`, `POST /sync`, `GET /summary` (read-only, reuses Google OAuth) |
| `/api/pages` | `pages/` | `GET /`, `GET /{id}`, `GET /{id}/content`, `GET /{id}/links` |
| `/api/content` | `content/` | `GET /drafts`, `POST /drafts/generate`, `GET · PUT /drafts/{id}`, `POST /drafts/{id}/approve` |
| `/api/keywords` | `keywords/` | `GET · POST /`, `PATCH · DELETE /{id}` |
| `/api/seo/analysis` | `seo_analysis/` | `POST /run`, `GET /results/{run_id}` |
| `/api/opportunities` | `seo_opportunities/` | `GET /`, `GET /{id}` |
| `/api/audit` | `content_audit/` | `GET /`, `PATCH /{page_id}/verdict` |
| `/api/ideas` | `content_ideas/` | `GET · POST /`, `POST /{id}/validate`, `PATCH /{id}/status` |
| `/api/research/sources` | `research/` | `GET · POST /`, `POST /from-file` (local drag-and-drop), `GET /{id}`, `POST /{id}/extract`, `GET /{id}/topics · /claims · /questions` |
| `/api/discussions` | `discussion/` | `GET · POST /`, `GET /{id}/messages`, `POST /{id}/messages`, `POST /{id}/decisions` |
| `/api/article-plans` | `article_planner/` | `GET · POST /`, `GET · PATCH /{id}`, `POST /{id}/prompt`, `POST /{id}/fact-check` |
| `/api/references` | `references/` | `GET · POST /`, `POST /{id}/verify` |
| `/api/rules` | `seo_rules/` (module-scoped) | `GET /`, `PATCH /{code}`, `POST /evaluate` |
| `/api/findings` | `seo_analysis/` | `GET /`, `GET /{id}`, `PATCH /{id}/status`, `POST /{id}/actions` |
| `/api/topic-clusters` | `topic_clusters/` | `GET · POST /`, `PUT /{id}/pages` |
| `/api/internal-links` | `internal_links/` | `GET /`, `PATCH /{id}/status` |
| `/api/reports` | `reports/` | `GET /`, `POST /generate` |
| `/api/publishing` | `publishing/` | `GET · PUT /config/{target}`, `POST /wordpress`, `POST /github`, `GET /logs` (approved drafts only) |
| `/api/ai-providers` | `settings/` | `GET · POST /`, `PATCH /{id}`, `POST /{id}/test` |
| `/api/settings` | `settings/` | `GET /`, `PUT /{key}` |
| `/api/diagnostics` | `diagnostics/` | `GET · POST /events` (local usage analytics), `POST /crash`, `GET /info` (connectivity/proxy/log state) |

---

## Dependency Injection

```python
# backend/app/api/dependencies.py
from typing import Annotated
from fastapi import Depends
from app.database.connection import get_session

# 1. DB session — one per request, committed by the router layer
DbSession = Annotated[Session, Depends(get_session)]

# 2. Resolved website — 404s centrally instead of per-route checks
async def get_website(website_id: int, db: DbSession) -> Website: ...
WebsiteDep = Annotated[Website, Depends(get_website)]

# 3. Pagination — uniform list endpoints
async def get_pagination(page: int = 1, page_size: int = 50) -> Pagination: ...
PaginationDep = Annotated[Pagination, Depends(get_pagination)]

# 4. AI provider — resolved from settings (default provider), injected into services
async def get_ai_provider(db: DbSession) -> AIProvider: ...
```

Services are instantiated per request with injected deps:

```python
def get_websites_service(db: DbSession) -> WebsiteService:
    return WebsiteService(repository=WebsiteRepository(db))

WebsitesServiceDep = Annotated[WebsiteService, Depends(get_websites_service)]
```

---

## Conventions

### Requests & responses

- All bodies/params validated by **Pydantic schemas** (`schemas.py` per module); ORM objects never leak to HTTP.
- JSON keys: `snake_case`, matching column names where sensible.
- List endpoints return:

```json
{ "items": [ ... ], "total": 123, "page": 1, "page_size": 50 }
```

- Timestamps: ISO-8601 UTC strings.

### Errors

Single error envelope, produced by `core/exceptions.py` handlers:

```json
{ "error": { "code": "website.not_found", "message": "Website 42 does not exist", "details": {} } }
```

| HTTP | Use |
|------|-----|
| 400 | Validation / business rule violation |
| 404 | Entity not found (`<module>.not_found`) |
| 409 | Conflict (duplicate URL, already connected) |
| 422 | Pydantic validation (FastAPI default) |
| 502 | Upstream integration failure (Google, WordPress...) — original error in `details` |

### Long-running jobs

Crawl, imports, and extractions are async jobs:

```text
POST /api/websites/{id}/crawl/start   → 202 { "job_id": ... }
GET  /api/websites/{id}/crawl/status  → { "status": "running", "progress": 0.4 }
```

Job history persists in `sync_logs` (Rule 7 — raw output path recorded).

### Security

- Backend binds to `127.0.0.1` only; Tauri passes a per-launch token checked by middleware.
- Secrets (API keys, OAuth tokens) encrypted via Tauri secure storage; DB stores references/ciphertext only.

---

## Implementation Order

Matches development phases — routers are added only when their phase starts:

| Phase | Routers added |
|-------|---------------|
| 1 | `/api/health` |
| 2 | `/api/websites`, crawl endpoints, `/api/pages` |
| 3 | `/api/search-console` |
| 4 | `/api/seo/analysis`, `/api/findings`, `/api/rules`, `/api/references` |
| 5 | `/api/opportunities` |
| 6 | `/api/audit` |
| 7 | `/api/research/sources`, `/api/ideas` |
| 8 | `/api/discussions`, `/api/ai-providers` |
| 9 | `/api/article-plans` |
| 11 | `/api/topic-clusters`, `/api/internal-links`, `/api/reports` |
