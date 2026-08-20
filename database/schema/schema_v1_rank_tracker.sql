-- Schema v1: Keyword Rank Tracker
-- Track keyword positions over time with daily snapshots and trend analysis

CREATE TABLE IF NOT EXISTS tracked_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    target_url TEXT,
    group_name TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rank_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    position INTEGER,
    previous_position INTEGER,
    change INTEGER,  -- positive = improved, negative = dropped
    search_volume INTEGER,
    clicks INTEGER,
    impressions INTEGER,
    ctr REAL,
    url TEXT,  -- actual ranking URL
    search_engine TEXT DEFAULT 'google',
    country TEXT DEFAULT 'us',
    device TEXT DEFAULT 'desktop',  -- desktop, mobile
    snapshot_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (keyword_id) REFERENCES tracked_keywords(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rank_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,  -- position_change, new_keyword, lost_ranking
    old_position INTEGER,
    new_position INTEGER,
    change INTEGER,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (keyword_id) REFERENCES tracked_keywords(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tracked_keywords_website ON tracked_keywords(website_id, keyword);
CREATE INDEX IF NOT EXISTS idx_rank_snapshots_keyword ON rank_snapshots(keyword_id);
CREATE INDEX IF NOT EXISTS idx_rank_snapshots_date ON rank_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_rank_alerts_keyword ON rank_alerts(keyword_id);
