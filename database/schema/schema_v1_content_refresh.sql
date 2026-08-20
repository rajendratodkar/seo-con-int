-- Schema v1: Content Refresh Scheduler
-- Detects stale content and generates prioritized refresh recommendations

CREATE TABLE IF NOT EXISTS refresh_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    min_age_days INTEGER NOT NULL DEFAULT 90,
    traffic_drop_pct REAL NOT NULL DEFAULT 10.0,
    staleness_weight REAL NOT NULL DEFAULT 1.0,
    traffic_weight REAL NOT NULL DEFAULT 1.0,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS refresh_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    page_id INTEGER NOT NULL,
    rule_id INTEGER,
    priority_score REAL NOT NULL DEFAULT 0,
    priority_date TEXT,
    reason TEXT,
    suggested_changes TEXT,        -- JSON array of {type, current, suggested}
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed, skipped
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES refresh_rules(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS refresh_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    page_id INTEGER NOT NULL,
    action TEXT NOT NULL,           -- refreshed, skipped, updated
    changes_made TEXT,              -- JSON of what was changed
    clicks_before INTEGER,
    clicks_after INTEGER,
    impressions_before INTEGER,
    impressions_after INTEGER,
    position_before REAL,
    position_after REAL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (schedule_id) REFERENCES refresh_schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refresh_rules_website ON refresh_rules(website_id);
CREATE INDEX IF NOT EXISTS idx_refresh_schedules_website ON refresh_schedules(website_id);
CREATE INDEX IF NOT EXISTS idx_refresh_schedules_page ON refresh_schedules(page_id);
CREATE INDEX IF NOT EXISTS idx_refresh_schedules_status ON refresh_schedules(status);
CREATE INDEX IF NOT EXISTS idx_refresh_history_schedule ON refresh_history(schedule_id);
CREATE INDEX IF NOT EXISTS idx_refresh_history_page ON refresh_history(page_id);
