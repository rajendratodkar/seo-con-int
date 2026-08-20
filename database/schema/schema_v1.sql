-- =============================================================================
-- SEO Content Intelligence — Database Schema v1 (SQLite)
-- =============================================================================
-- Design principles (from plan.md §25):
--   * Raw data is never overwritten: raw -> normalized -> analysis
--     (raw API payloads land in data/raw/ + search_console_raw, analysis
--      results live in seo_findings / seo_actions)
--   * Database != analysis: tables store facts, engines compute results
--   * Tables are created in stages at runtime; this file defines the target
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 0. SYSTEM (sync_logs defined first — referenced by search_console_raw)
-- -----------------------------------------------------------------------------

-- Import/crawl job history (Rule 7: raw file paths kept for recalculation)
CREATE TABLE IF NOT EXISTS sync_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    module           TEXT    NOT NULL,                   -- search_console | crawler | wordpress | youtube | podcast
    entity_id        INTEGER,                            -- id in the module's primary table
    sync_type        TEXT    NOT NULL,                   -- historical | incremental | crawl | extract
    status           TEXT    NOT NULL DEFAULT 'running', -- running | completed | failed
    started_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    finished_at      TEXT,
    records_imported INTEGER NOT NULL DEFAULT 0,
    error_message    TEXT,
    raw_file_path    TEXT,                               -- location of raw dump under data/raw/
    created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_module ON sync_logs(module);

-- -----------------------------------------------------------------------------
-- 1. WEBSITES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS websites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    url         TEXT    NOT NULL UNIQUE,
    platform    TEXT    NOT NULL DEFAULT 'unknown',   -- wordpress | astro | static | unknown | other
    sitemap_url TEXT,
    status      TEXT    NOT NULL DEFAULT 'active',    -- active | inactive | error
    settings    TEXT,                                  -- JSON: per-website configuration
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS website_connections (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id       INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    connection_type  TEXT    NOT NULL,                 -- search_console | wordpress | github
    status           TEXT    NOT NULL DEFAULT 'disconnected',  -- disconnected | connected | error
    config           TEXT,                             -- JSON: credentials ref, endpoints, options
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, connection_type)
);

CREATE INDEX IF NOT EXISTS idx_website_connections_website ON website_connections(website_id);

-- -----------------------------------------------------------------------------
-- 2. SEARCH CONSOLE
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS search_console_properties (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id        INTEGER REFERENCES websites(id) ON DELETE SET NULL,  -- NULL until bound
    site_url          TEXT    NOT NULL UNIQUE,          -- GSC property identifier (sc-domain: or URL prefix)
    permission_level  TEXT,                             -- siteOwner | siteFullUser | siteRestrictedUser
    status            TEXT    NOT NULL DEFAULT 'discovered',  -- discovered | connected | error
    connected_at      TEXT,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Normalized Search Console performance data (imported, never recalculated in place)
CREATE TABLE IF NOT EXISTS search_console_data (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    property_id   INTEGER NOT NULL REFERENCES search_console_properties(id) ON DELETE CASCADE,
    date          TEXT    NOT NULL,                     -- YYYY-MM-DD
    query         TEXT,                                 -- NULL for page-only dimension sets
    page_url      TEXT,
    clicks        INTEGER NOT NULL DEFAULT 0,
    impressions   INTEGER NOT NULL DEFAULT 0,
    ctr           REAL    NOT NULL DEFAULT 0,
    position      REAL    NOT NULL DEFAULT 0,
    device        TEXT,                                 -- DESKTOP | MOBILE | TABLET (nullable)
    country       TEXT,                                 -- nullable
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (property_id, date, query, page_url, device, country)
);

CREATE INDEX IF NOT EXISTS idx_sc_data_website_date ON search_console_data(website_id, date);
CREATE INDEX IF NOT EXISTS idx_sc_data_query       ON search_console_data(query);
CREATE INDEX IF NOT EXISTS idx_sc_data_page        ON search_console_data(page_url);

-- Raw API payloads (Rule 7: keep raw data — enables recalculation later)
CREATE TABLE IF NOT EXISTS search_console_raw (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id   INTEGER NOT NULL REFERENCES search_console_properties(id) ON DELETE CASCADE,
    sync_log_id   INTEGER REFERENCES sync_logs(id) ON DELETE SET NULL,
    request_dims  TEXT,                                  -- JSON: dimensions/period requested
    payload       TEXT    NOT NULL,                      -- JSON: untouched API response
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sc_raw_property ON search_console_raw(property_id);

-- -----------------------------------------------------------------------------
-- 3. PAGES (crawled inventory)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id       INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    url              TEXT    NOT NULL,
    canonical_url    TEXT,
    title            TEXT,
    meta_description TEXT,
    status_code      INTEGER,                            -- HTTP status from last crawl
    published_at     TEXT,
    modified_at      TEXT,
    crawl_status     TEXT    NOT NULL DEFAULT 'pending', -- pending | crawling | done | failed
    last_crawled_at  TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, url)
);

CREATE INDEX IF NOT EXISTS idx_pages_website ON pages(website_id);

-- 1:1 heavy content payload, kept out of `pages` for query performance
CREATE TABLE IF NOT EXISTS page_content (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id      INTEGER NOT NULL UNIQUE REFERENCES pages(id) ON DELETE CASCADE,
    text_content TEXT,
    headings     TEXT,                                   -- JSON: [{level, text}, ...]
    images       TEXT,                                   -- JSON: [{src, alt}, ...]
    word_count   INTEGER,
    schema_json  TEXT,                                   -- JSON-LD structured data found on page
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS page_links (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id        INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    target_url     TEXT    NOT NULL,
    target_page_id INTEGER REFERENCES pages(id) ON DELETE SET NULL,  -- resolved when internal
    anchor_text    TEXT,
    is_internal    INTEGER NOT NULL DEFAULT 0,           -- 0 | 1
    is_nofollow    INTEGER NOT NULL DEFAULT 0,           -- 0 | 1
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_page_links_page   ON page_links(page_id);
CREATE INDEX IF NOT EXISTS idx_page_links_target ON page_links(target_page_id);

-- -----------------------------------------------------------------------------
-- 4. KEYWORDS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS keywords (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    keyword       TEXT    NOT NULL,
    normalized    TEXT,                                  -- lowercase/trimmed form for joins to SC queries
    search_intent TEXT,                                  -- informational | transactional | navigational | commercial
    group_name    TEXT,                                  -- grouping / clustering aid
    source        TEXT    NOT NULL DEFAULT 'manual',     -- search_console | manual | research
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, normalized)
);

CREATE INDEX IF NOT EXISTS idx_keywords_website ON keywords(website_id);

-- -----------------------------------------------------------------------------
-- 5. RESEARCH & IDEAS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_sources (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id          INTEGER REFERENCES websites(id) ON DELETE SET NULL,
    source_type         TEXT    NOT NULL,                -- youtube | podcast | article | news | manual | search_console
    url                 TEXT,
    title               TEXT,
    availability_status TEXT    NOT NULL DEFAULT 'pending',  -- full | transcript_unavailable | metadata_only | pending
    extraction_status   TEXT    NOT NULL DEFAULT 'pending',  -- pending | processing | completed | failed
    error_message       TEXT,
    raw_data            TEXT,                            -- JSON: untouched extracted payload
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_research_sources_type ON research_sources(source_type);

CREATE TABLE IF NOT EXISTS research_topics (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id  INTEGER NOT NULL REFERENCES research_sources(id) ON DELETE CASCADE,
    topic      TEXT    NOT NULL,
    importance REAL    NOT NULL DEFAULT 0,               -- 0..1
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_research_topics_source ON research_topics(source_id);

CREATE TABLE IF NOT EXISTS research_claims (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id  INTEGER NOT NULL REFERENCES research_sources(id) ON DELETE CASCADE,
    claim_text TEXT    NOT NULL,
    evidence   TEXT,                                     -- quote / timestamp / locator backing the claim
    confidence TEXT    NOT NULL DEFAULT 'medium',        -- high | medium | low
    verified   INTEGER NOT NULL DEFAULT 0,               -- 0 | 1 (human fact-check)
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_research_claims_source ON research_claims(source_id);

CREATE TABLE IF NOT EXISTS research_questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id  INTEGER REFERENCES research_sources(id) ON DELETE CASCADE,
    question   TEXT    NOT NULL,
    answered   INTEGER NOT NULL DEFAULT 0,               -- 0 | 1
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_research_questions_source ON research_questions(source_id);

CREATE TABLE IF NOT EXISTS content_ideas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER REFERENCES websites(id) ON DELETE CASCADE,
    source_type TEXT,                                    -- youtube | podcast | search_console | website | news | manual
    source_id   INTEGER,                                 -- polymorphic: id in the source's table
    title       TEXT    NOT NULL,
    description TEXT,
    status      TEXT    NOT NULL DEFAULT 'draft',        -- draft | validated | approved | rejected
    score       REAL,                                    -- 0..1 idea score
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_content_ideas_website ON content_ideas(website_id);

-- -----------------------------------------------------------------------------
-- 6. DISCUSSION
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discussions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER REFERENCES websites(id) ON DELETE SET NULL,
    idea_id    INTEGER REFERENCES content_ideas(id) ON DELETE SET NULL,
    topic      TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'open',          -- open | decided | archived
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_discussions_idea ON discussions(idea_id);

CREATE TABLE IF NOT EXISTS discussion_messages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
    role          TEXT    NOT NULL,                      -- user | ai
    content       TEXT    NOT NULL,
    provider      TEXT,                                  -- openai | gemini | anthropic (NULL for user)
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_discussion_messages_disc ON discussion_messages(discussion_id);

CREATE TABLE IF NOT EXISTS discussion_decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
    decision      TEXT    NOT NULL,
    rationale     TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_discussion_decisions_disc ON discussion_decisions(discussion_id);

-- -----------------------------------------------------------------------------
-- 7. ARTICLE PLANNER
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS article_plans (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id         INTEGER REFERENCES websites(id) ON DELETE SET NULL,
    idea_id            INTEGER REFERENCES content_ideas(id) ON DELETE SET NULL,
    discussion_id      INTEGER REFERENCES discussions(id) ON DELETE SET NULL,
    title              TEXT    NOT NULL,
    primary_topic      TEXT,
    search_intent      TEXT,                             -- informational | transactional | navigational | commercial
    audience           TEXT,
    outline            TEXT,                             -- JSON: ordered sections
    questions          TEXT,                             -- JSON: questions the article must answer
    internal_links     TEXT,                             -- JSON: suggested internal link targets
    sources            TEXT,                             -- JSON: reference ids / URLs
    facts_to_verify    TEXT,                             -- JSON: claims flagged for fact-check
    sc_evidence        TEXT,                             -- JSON: Search Console metrics backing the plan
    source_inspiration TEXT,                             -- JSON: research_source ids that inspired it
    things_to_avoid    TEXT,                             -- JSON
    status             TEXT    NOT NULL DEFAULT 'draft', -- draft | brief_ready | drafting | approved
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_article_plans_website ON article_plans(website_id);

-- AI-generated drafts (Rule 5: always labeled ai_suggestion, human approves before publish)
CREATE TABLE IF NOT EXISTS article_drafts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id      INTEGER NOT NULL REFERENCES article_plans(id) ON DELETE CASCADE,
    version      INTEGER NOT NULL DEFAULT 1,
    content      TEXT    NOT NULL,                      -- markdown draft
    content_path TEXT,                                   -- copy under data/content/
    ai_provider  TEXT,                                   -- provider that produced it (labeled, never hidden)
    ai_model     TEXT,
    status       TEXT    NOT NULL DEFAULT 'ai_suggestion',  -- ai_suggestion | human_edited | approved
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (plan_id, version)
);

CREATE INDEX IF NOT EXISTS idx_article_drafts_plan ON article_drafts(plan_id);

-- Publishing history (Rule 7: every outbound action is logged with raw response)
CREATE TABLE IF NOT EXISTS publish_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id      INTEGER NOT NULL REFERENCES article_drafts(id) ON DELETE CASCADE,
    target        TEXT    NOT NULL,               -- wordpress | github
    action        TEXT    NOT NULL,               -- draft | publish | commit
    status        TEXT    NOT NULL,               -- success | failed
    remote_id     TEXT,                            -- WP post id / commit sha
    remote_url    TEXT,
    response_path TEXT,                            -- raw upstream response (raw kept forever)
    error         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_publish_logs_draft ON publish_logs(draft_id);

-- -----------------------------------------------------------------------------
-- 8. REFERENCES & SEO RULES & FINDINGS
-- -----------------------------------------------------------------------------

-- Named reference_docs (not `references` — reserved SQL keyword)
CREATE TABLE IF NOT EXISTS reference_docs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT    NOT NULL,                        -- google_seo | google_search_console | google_structured_data |
                                                         -- google_spam_policies | sebi | amfi | rbi | income_tax | amc | other_official
    title       TEXT    NOT NULL,
    url         TEXT,
    verified_at TEXT,                                    -- last time the document was verified reachable/current
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (category, title)
);

CREATE TABLE IF NOT EXISTS seo_rules (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code    TEXT    NOT NULL UNIQUE,                -- e.g. META-001
    name         TEXT    NOT NULL,
    description  TEXT,
    category     TEXT    NOT NULL,                       -- technical | content | financial
    severity     TEXT    NOT NULL DEFAULT 'warning',     -- info | warning | critical
    reference_id INTEGER REFERENCES reference_docs(id) ON DELETE SET NULL,   -- Rule -> Reference -> Official document
    enabled      INTEGER NOT NULL DEFAULT 1,             -- 0 | 1
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_seo_rules_reference ON seo_rules(reference_id);

-- Recommendations / findings (Rule 5 & 6: every recommendation carries why + evidence)
CREATE TABLE IF NOT EXISTS seo_findings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id     INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    page_id        INTEGER REFERENCES pages(id) ON DELETE CASCADE,
    rule_id        INTEGER REFERENCES seo_rules(id) ON DELETE SET NULL,
    recommendation TEXT    NOT NULL,                     -- What to do
    why            TEXT    NOT NULL,                     -- Why
    evidence       TEXT    NOT NULL,                     -- human-readable evidence summary
    data           TEXT,                                 -- JSON: raw numbers behind the evidence
    reference_id   INTEGER REFERENCES reference_docs(id) ON DELETE SET NULL,
    confidence     TEXT    NOT NULL DEFAULT 'medium',    -- high | medium | low
    severity       TEXT    NOT NULL DEFAULT 'warning',   -- info | warning | critical
    rec_type       TEXT    NOT NULL,                     -- data_based | rule_based | ai_suggestion
    status         TEXT    NOT NULL DEFAULT 'open',      -- open | accepted | dismissed | resolved
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_seo_findings_website ON seo_findings(website_id);
CREATE INDEX IF NOT EXISTS idx_seo_findings_page    ON seo_findings(page_id);
CREATE INDEX IF NOT EXISTS idx_seo_findings_rule    ON seo_findings(rule_id);

CREATE TABLE IF NOT EXISTS seo_actions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id    INTEGER NOT NULL REFERENCES seo_findings(id) ON DELETE CASCADE,
    action        TEXT    NOT NULL,                      -- concrete suggested action text
    status        TEXT    NOT NULL DEFAULT 'pending',    -- pending | done | dismissed
    completed_at  TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_seo_actions_finding ON seo_actions(finding_id);

-- -----------------------------------------------------------------------------
-- 9. TOPIC CLUSTERS & INTERNAL LINKS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS topic_clusters (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    name          TEXT    NOT NULL,
    description   TEXT,
    pillar_page_id INTEGER REFERENCES pages(id) ON DELETE SET NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_topic_clusters_website ON topic_clusters(website_id);

-- Junction: pages belonging to a cluster
CREATE TABLE IF NOT EXISTS topic_cluster_pages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL REFERENCES topic_clusters(id) ON DELETE CASCADE,
    page_id    INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cluster_id, page_id)
);

-- Planned/recommended internal links (crawled links live in page_links)
CREATE TABLE IF NOT EXISTS internal_links (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id     INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    source_page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    target_page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    recommendation TEXT,                                 -- why this link is suggested
    status         TEXT    NOT NULL DEFAULT 'suggested', -- suggested | applied | dismissed
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, source_page_id, target_page_id)
);

CREATE INDEX IF NOT EXISTS idx_internal_links_website ON internal_links(website_id);

-- -----------------------------------------------------------------------------
-- 10. SYSTEM (settings & ai_providers)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_providers (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    provider          TEXT    NOT NULL UNIQUE,           -- openai | gemini | anthropic
    display_name      TEXT    NOT NULL,
    api_key_encrypted TEXT,                              -- encrypted at rest (Tauri secure storage / key ref)
    model             TEXT,                              -- default model id
    is_default        INTEGER NOT NULL DEFAULT 0,        -- 0 | 1
    enabled           INTEGER NOT NULL DEFAULT 0,        -- 0 | 1
    config            TEXT,                              -- JSON: temperature, max tokens, etc.
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT    NOT NULL UNIQUE,
    value      TEXT,                                     -- JSON-safe string
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------------------------
-- 11. GOOGLE ANALYTICS (connection + normalized daily metrics; raw archived on disk)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ga_connections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL UNIQUE REFERENCES websites(id) ON DELETE CASCADE,
    property_id   TEXT    NOT NULL,                     -- GA4 numeric property id
    property_name TEXT,
    status        TEXT    NOT NULL DEFAULT 'connected', -- connected | error
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ga_metrics_daily (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    date          TEXT    NOT NULL,                     -- YYYY-MM-DD
    sessions      INTEGER NOT NULL DEFAULT 0,
    active_users  INTEGER NOT NULL DEFAULT 0,
    pageviews     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, date)
);

CREATE INDEX IF NOT EXISTS idx_ga_metrics_daily_website ON ga_metrics_daily(website_id, date);

-- Local usage analytics (feature clicks only; capped by the diagnostics service)
CREATE TABLE IF NOT EXISTS usage_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event      TEXT    NOT NULL,                     -- page_view | action | crash
    detail     TEXT,                                  -- route / button id / crash message
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_events_created ON usage_events(created_at);
