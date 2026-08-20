-- =============================================================================
-- Content Calendar — schema extension
-- =============================================================================
-- Schedule content, track deadlines, and visualize the publishing pipeline.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- CALENDAR EVENTS — scheduled content items
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS calendar_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    title           TEXT    NOT NULL,
    description     TEXT,
    event_type      TEXT    NOT NULL DEFAULT 'article',  -- article | review | publish | meeting | deadline
    status          TEXT    NOT NULL DEFAULT 'planned',   -- planned | in_progress | review | published | overdue | cancelled
    -- Scheduling
    start_date      TEXT    NOT NULL,  -- YYYY-MM-DD
    end_date        TEXT,              -- YYYY-MM-DD (optional, for multi-day events)
    -- Linked content (optional)
    plan_id         INTEGER REFERENCES article_plans(id) ON DELETE SET NULL,
    draft_id        INTEGER REFERENCES article_drafts(id) ON DELETE SET NULL,
    -- Metadata
    priority        TEXT    NOT NULL DEFAULT 'normal',  -- low | normal | high | urgent
    color           TEXT,                               -- hex color for calendar display
    assignee        TEXT,                               -- who is responsible
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_website ON calendar_events(website_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_dates   ON calendar_events(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_status  ON calendar_events(status);
