-- =============================================================================
-- Content Rewriter — schema extension
-- =============================================================================
-- AI-powered content optimization: rewrite titles, descriptions, headings.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- REWRITE REQUESTS — history of rewrites
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS rewrite_requests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER REFERENCES websites(id) ON DELETE SET NULL,
    page_id         INTEGER REFERENCES pages(id) ON DELETE SET NULL,
    content_type    TEXT    NOT NULL,   -- title | description | heading | custom
    original_text   TEXT    NOT NULL,
    context         TEXT,              -- additional context (page topic, target keyword, etc.)
    provider        TEXT,              -- openai | gemini | anthropic
    model           TEXT,
    -- Results
    rewrites        TEXT    NOT NULL DEFAULT '[]',  -- JSON: list of rewrite options
    selected_index  INTEGER,           -- which rewrite was selected (0-based)
    applied         INTEGER NOT NULL DEFAULT 0,   -- 0 | 1
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rewrite_requests_website ON rewrite_requests(website_id);
CREATE INDEX IF NOT EXISTS idx_rewrite_requests_page    ON rewrite_requests(page_id);
