-- Schema v1: SERP A/B Testing
-- Test different title/description combinations and measure CTR impact

CREATE TABLE IF NOT EXISTS serp_ab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    page_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, running, paused, completed, cancelled
    -- Control (original)
    control_title TEXT NOT NULL,
    control_description TEXT NOT NULL,
    control_clicks INTEGER DEFAULT 0,
    control_impressions INTEGER DEFAULT 0,
    control_ctr REAL DEFAULT 0,
    control_avg_position REAL DEFAULT 0,
    -- Variant (new)
    variant_title TEXT NOT NULL,
    variant_description TEXT NOT NULL,
    variant_clicks INTEGER DEFAULT 0,
    variant_impressions INTEGER DEFAULT 0,
    variant_ctr REAL DEFAULT 0,
    variant_avg_position REAL DEFAULT 0,
    -- Results
    winner TEXT,  -- control, variant, inconclusive
    confidence REAL,
    z_score REAL,
    p_value REAL,
    lift REAL,  -- CTR improvement percentage
    -- Settings
    min_duration_days INTEGER DEFAULT 7,
    confidence_level REAL DEFAULT 0.95,
    -- Dates
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS serp_ab_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    variant TEXT NOT NULL,  -- control, variant
    snapshot_date TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    avg_position REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (test_id) REFERENCES serp_ab_tests(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_serp_ab_tests_website ON serp_ab_tests(website_id);
CREATE INDEX IF NOT EXISTS idx_serp_ab_tests_page ON serp_ab_tests(page_id);
CREATE INDEX IF NOT EXISTS idx_serp_ab_snapshots_test ON serp_ab_snapshots(test_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_serp_ab_snapshots_unique ON serp_ab_snapshots(test_id, variant, snapshot_date);
