-- Schema v1: Redirect Management
-- Track 301/302 redirects, detect broken links, manage redirect chains

CREATE TABLE IF NOT EXISTS redirects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    target_url TEXT NOT NULL,
    status_code INTEGER NOT NULL DEFAULT 301,  -- 301, 302, 307, 308
    is_active INTEGER NOT NULL DEFAULT 1,
    chain_depth INTEGER DEFAULT 0,  -- 0 = direct, 1+ = chain
    hit_count INTEGER DEFAULT 0,  -- times this redirect was followed
    last_checked_at TEXT,
    last_status_code INTEGER,  -- actual response code when checked
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS redirect_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    redirect_id INTEGER NOT NULL,
    checked_at TEXT DEFAULT (datetime('now')),
    status_code INTEGER,
    response_time_ms INTEGER,
    final_url TEXT,
    error_message TEXT,
    FOREIGN KEY (redirect_id) REFERENCES redirects(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_redirects_source ON redirects(website_id, source_url);
CREATE INDEX IF NOT EXISTS idx_redirects_website ON redirects(website_id);
CREATE INDEX IF NOT EXISTS idx_redirect_checks_redirect ON redirect_checks(redirect_id);
