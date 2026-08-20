-- =============================================================================
-- Page Speed Insights — schema extension
-- =============================================================================
-- Track Core Web Vitals and performance scores per page over time.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- PAGE SPEED SNAPSHOTS — historical performance data per page
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS page_speed_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    page_id         INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    url             TEXT    NOT NULL,
    -- Core Web Vitals
    lcp             REAL,              -- Largest Contentful Paint (seconds)
    fid             REAL,              -- First Input Delay (milliseconds)
    cls             REAL,              -- Cumulative Layout Shift
    fcp             REAL,              -- First Contentful Paint (seconds)
    ttfb            REAL,              -- Time to First Byte (seconds)
    tti             REAL,              -- Time to Interactive (seconds)
    -- Scores (0-100)
    performance_score INTEGER,         -- Lighthouse performance score
    accessibility_score INTEGER,
    best_practices_score INTEGER,
    seo_score       INTEGER,
    -- Opportunities & diagnostics
    opportunities   TEXT,              -- JSON: list of opportunities with savings
    diagnostics     TEXT,              -- JSON: diagnostic info
    -- Source
    source          TEXT    NOT NULL DEFAULT 'manual',  -- manual | pagespeed_api | lighthouse
    checked_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_page_speed_page     ON page_speed_snapshots(page_id);
CREATE INDEX IF NOT EXISTS idx_page_speed_website  ON page_speed_snapshots(website_id);
CREATE INDEX IF NOT EXISTS idx_page_speed_checked  ON page_speed_snapshots(checked_at);
