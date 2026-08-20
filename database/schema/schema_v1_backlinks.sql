-- =============================================================================
-- Backlink Monitor — schema extension
-- =============================================================================
-- Track inbound links, domain authority, and link changes over time.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- BACKLINKS — known inbound links
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS backlinks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    source_url      TEXT    NOT NULL,
    source_domain   TEXT    NOT NULL,
    target_url      TEXT    NOT NULL,
    anchor_text     TEXT,
    is_nofollow     INTEGER NOT NULL DEFAULT 0,
    is_sponsored    INTEGER NOT NULL DEFAULT 0,
    domain_authority INTEGER,          -- 0-100 (if available)
    page_authority  INTEGER,           -- 0-100 (if available)
    status          TEXT    NOT NULL DEFAULT 'active',  -- active | lost | broken
    first_seen      TEXT    NOT NULL DEFAULT (datetime('now')),
    last_checked    TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, source_url, target_url)
);

CREATE INDEX IF NOT EXISTS idx_backlinks_website ON backlinks(website_id);
CREATE INDEX IF NOT EXISTS idx_backlinks_domain  ON backlinks(source_domain);
CREATE INDEX IF NOT EXISTS idx_backlinks_status  ON backlinks(status);

-- -----------------------------------------------------------------------------
-- BACKLINK CHANGES — historical log of gained/lost links
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS backlink_changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    backlink_id     INTEGER REFERENCES backlinks(id) ON DELETE SET NULL,
    change_type     TEXT    NOT NULL,  -- gained | lost | updated
    source_url      TEXT    NOT NULL,
    target_url      TEXT    NOT NULL,
    details         TEXT,              -- JSON: what changed
    detected_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_backlink_changes_website ON backlink_changes(website_id);
CREATE INDEX IF NOT EXISTS idx_backlink_changes_date    ON backlink_changes(detected_at);
