-- =============================================================================
-- SEO Checklist — schema extension
-- =============================================================================
-- Per-page SEO checklists with status tracking.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- SEO CHECKLISTS — one checklist per page
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS seo_checklists (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    page_id         INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    status          TEXT    NOT NULL DEFAULT 'in_progress',  -- in_progress | completed | archived
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (website_id, page_id)
);

CREATE INDEX IF NOT EXISTS idx_seo_checklists_website ON seo_checklists(website_id);
CREATE INDEX IF NOT EXISTS idx_seo_checklists_page    ON seo_checklists(page_id);

-- -----------------------------------------------------------------------------
-- SEO CHECKLIST ITEMS — individual tasks
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS seo_checklist_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_id    INTEGER NOT NULL REFERENCES seo_checklists(id) ON DELETE CASCADE,
    category        TEXT    NOT NULL,   -- meta | content | technical | links | structured_data | performance
    item_text       TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'todo',  -- todo | done | skipped | blocked
    finding_id      INTEGER REFERENCES seo_findings(id) ON DELETE SET NULL,  -- linked finding (if auto-generated)
    notes           TEXT,
    completed_at    TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_checklist_items_checklist ON seo_checklist_items(checklist_id);
CREATE INDEX IF NOT EXISTS idx_checklist_items_status    ON seo_checklist_items(status);
