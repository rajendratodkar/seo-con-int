-- =============================================================================
-- Sitemap Generator — schema extension
-- =============================================================================
-- Generate XML sitemaps from crawled pages with priority and changefreq.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- SITEMAP SETTINGS — per-website sitemap configuration
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sitemap_settings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL UNIQUE REFERENCES websites(id) ON DELETE CASCADE,
    default_priority REAL   NOT NULL DEFAULT 0.5,
    default_changefreq TEXT NOT NULL DEFAULT 'weekly',
    include_images   INTEGER NOT NULL DEFAULT 1,  -- 0 | 1
    include_news     INTEGER NOT NULL DEFAULT 0,  -- 0 | 1
    max_urls         INTEGER NOT NULL DEFAULT 50000,
    exclude_patterns TEXT,                        -- JSON: list of URL patterns to exclude
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------------------------
-- SITEMAP URL OVERRIDES — per-page priority/changefreq
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sitemap_url_overrides (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    url_pattern     TEXT    NOT NULL,    -- URL path pattern (e.g. /blog/*)
    priority        REAL,
    changefreq      TEXT,
    include         INTEGER NOT NULL DEFAULT 1,  -- 0 | 1
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, url_pattern)
);

CREATE INDEX IF NOT EXISTS idx_sitemap_overrides_website ON sitemap_url_overrides(website_id);
