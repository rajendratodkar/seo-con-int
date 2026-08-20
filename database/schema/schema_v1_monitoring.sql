-- =============================================================================
-- Monitoring & Alerts — schema extension
-- =============================================================================
-- Adds tables for configurable monitoring rules, alert channels, and history.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- MONITORING RULES — what to watch
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS monitoring_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,
    rule_type       TEXT    NOT NULL,  -- ranking_drop | traffic_drop | new_seo_issue | crawl_error | position_change | ctr_drop
    enabled         INTEGER NOT NULL DEFAULT 1,
    -- Thresholds (JSON for flexibility)
    config          TEXT    NOT NULL DEFAULT '{}',
    -- e.g. {"threshold_pct": 15, "min_impressions": 50, "lookback_days": 7}
    channel_ids     TEXT    NOT NULL DEFAULT '[]',  -- JSON array of alert_channel ids
    -- Schedule
    check_interval  TEXT    NOT NULL DEFAULT 'daily',  -- hourly | daily | weekly
    last_checked_at TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_monitoring_rules_website ON monitoring_rules(website_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_rules_type    ON monitoring_rules(rule_type);

-- -----------------------------------------------------------------------------
-- ALERT CHANNELS — where to notify
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS alert_channels (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    channel_type  TEXT    NOT NULL,  -- email | slack | desktop
    enabled       INTEGER NOT NULL DEFAULT 1,
    -- Type-specific config (JSON)
    config        TEXT    NOT NULL DEFAULT '{}',
    -- email: {"smtp_host", "smtp_port", "username", "from_address", "to_addresses"}
    -- slack: {"webhook_url"}
    -- desktop: {} (uses Tauri notification)
    last_tested_at TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------------------------
-- ALERT HISTORY — log of every notification sent
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS alert_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id         INTEGER NOT NULL REFERENCES monitoring_rules(id) ON DELETE CASCADE,
    channel_id      INTEGER NOT NULL REFERENCES alert_channels(id) ON DELETE CASCADE,
    severity        TEXT    NOT NULL DEFAULT 'info',  -- info | warning | critical
    title           TEXT    NOT NULL,
    message         TEXT    NOT NULL,
    data            TEXT,  -- JSON: snapshot of what triggered the alert
    status          TEXT    NOT NULL DEFAULT 'sent',  -- sent | failed | suppressed
    error_message   TEXT,
    sent_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alert_history_rule    ON alert_history(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_sent    ON alert_history(sent_at);
CREATE INDEX IF NOT EXISTS idx_alert_history_channel ON alert_history(channel_id);

-- -----------------------------------------------------------------------------
-- MONITORING SNAPSHOTS — baseline data for comparison
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS monitoring_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    snapshot_type TEXT    NOT NULL,  -- rankings | traffic | seo_issues | crawl_status
    snapshot_date TEXT    NOT NULL,  -- YYYY-MM-DD
    data          TEXT    NOT NULL,  -- JSON: computed metrics
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, snapshot_type, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_monitoring_snapshots_website ON monitoring_snapshots(website_id, snapshot_type, snapshot_date);
