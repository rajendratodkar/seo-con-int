-- =============================================================================
-- Competitor Analysis — schema extension
-- =============================================================================
-- Track competitors, their rankings, and compute content gaps.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- COMPETITORS — websites we track
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS competitors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,
    url             TEXT    NOT NULL,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, url)
);

CREATE INDEX IF NOT EXISTS idx_competitors_website ON competitors(website_id);

-- -----------------------------------------------------------------------------
-- COMPETITOR RANKINGS — their keyword positions (manually entered or imported)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS competitor_rankings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id   INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    keyword         TEXT    NOT NULL,
    normalized      TEXT    NOT NULL,  -- lowercase/trimmed for joins
    position        REAL    NOT NULL DEFAULT 0,
    url             TEXT,             -- the page ranking for this keyword
    impressions     INTEGER,          -- estimated (if available)
    source          TEXT    NOT NULL DEFAULT 'manual',  -- manual | semrush | ahrefs | other
    snapshot_date   TEXT    NOT NULL,  -- YYYY-MM-DD when this was captured
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (competitor_id, normalized, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_comp_rankings_competitor ON competitor_rankings(competitor_id);
CREATE INDEX IF NOT EXISTS idx_comp_rankings_keyword    ON competitor_rankings(normalized);

-- -----------------------------------------------------------------------------
-- CONTENT GAPS — computed: keywords competitors rank for but we don't
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS content_gaps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    keyword         TEXT    NOT NULL,
    competitor_id   INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    competitor_pos  REAL    NOT NULL,
    competitor_url  TEXT,
    our_position    REAL,            -- NULL if we don't rank at all
    opportunity     TEXT    NOT NULL DEFAULT 'new_content',  -- new_content | improve_existing | quick_win
    search_volume   INTEGER,          -- estimated
    priority        REAL    NOT NULL DEFAULT 0,  -- 0..1 computed score
    status          TEXT    NOT NULL DEFAULT 'open',  -- open | reviewed | acted_on
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_content_gaps_website   ON content_gaps(website_id);
CREATE INDEX IF NOT EXISTS idx_content_gaps_priority  ON content_gaps(priority DESC);
CREATE INDEX IF NOT EXISTS idx_content_gaps_status    ON content_gaps(status);
