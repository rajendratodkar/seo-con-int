-- =============================================================================
-- A/B Testing — schema extension
-- =============================================================================
-- Track title/description/meta changes and measure their impact on CTR,
-- rankings, and traffic using Search Console data.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- AB TESTS — one test per page/element being changed
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ab_tests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    page_id         INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,
    element         TEXT    NOT NULL DEFAULT 'title',  -- title | description | both
    status          TEXT    NOT NULL DEFAULT 'draft',   -- draft | running | completed | cancelled
    -- Timeframe
    started_at      TEXT,
    completed_at    TEXT,
    min_duration_days INTEGER NOT NULL DEFAULT 7,       -- minimum days before declaring a winner
    -- Results (computed when test completes)
    winner          TEXT,                               -- 'control' | 'variant' | 'inconclusive'
    confidence      REAL,                               -- 0..1 statistical confidence
    result_summary  TEXT,                               -- JSON: detailed metrics
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ab_tests_website ON ab_tests(website_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_page    ON ab_tests(page_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status  ON ab_tests(status);

-- -----------------------------------------------------------------------------
-- AB VARIANTS — control (original) and variant (new version)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ab_variants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id       INTEGER NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
    variant_type  TEXT    NOT NULL,  -- control | variant
    title         TEXT,
    description   TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (test_id, variant_type)
);

CREATE INDEX IF NOT EXISTS idx_ab_variants_test ON ab_variants(test_id);

-- -----------------------------------------------------------------------------
-- AB DAILY SNAPSHOTS — per-variant daily metrics from Search Console
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ab_daily_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id         INTEGER NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
    variant_id      INTEGER NOT NULL REFERENCES ab_variants(id) ON DELETE CASCADE,
    date            TEXT    NOT NULL,  -- YYYY-MM-DD
    clicks          INTEGER NOT NULL DEFAULT 0,
    impressions     INTEGER NOT NULL DEFAULT 0,
    ctr             REAL    NOT NULL DEFAULT 0,
    position        REAL    NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (test_id, variant_id, date)
);

CREATE INDEX IF NOT EXISTS idx_ab_snapshots_test  ON ab_daily_snapshots(test_id, date);
CREATE INDEX IF NOT EXISTS idx_ab_snapshots_variant ON ab_daily_snapshots(variant_id);
