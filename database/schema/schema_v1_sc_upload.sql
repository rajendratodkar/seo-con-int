-- Schema v1: Search Console File Upload
-- Tracks file imports and stores imported data metadata

CREATE TABLE IF NOT EXISTS sc_imports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL,
    filename        TEXT    NOT NULL,
    file_type       TEXT    NOT NULL,           -- csv | json
    import_type     TEXT    NOT NULL,           -- performance | url_inspection | coverage | links
    rows_total      INTEGER NOT NULL DEFAULT 0,
    rows_imported   INTEGER NOT NULL DEFAULT 0,
    rows_skipped    INTEGER NOT NULL DEFAULT 0,
    rows_errors     INTEGER NOT NULL DEFAULT 0,
    error_details   TEXT,                       -- JSON: [{row, error}, ...]
    status          TEXT    NOT NULL DEFAULT 'pending',  -- pending | processing | completed | failed
    date_range_start TEXT,                      -- YYYY-MM-DD (earliest date in import)
    date_range_end  TEXT,                       -- YYYY-MM-DD (latest date in import)
    created_at      TEXT    DEFAULT (datetime('now')),
    completed_at    TEXT,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sc_imports_website ON sc_imports(website_id);
CREATE INDEX IF NOT EXISTS idx_sc_imports_status ON sc_imports(status);

-- URL Inspection data (imported from CSV export)
CREATE TABLE IF NOT EXISTS sc_url_inspection (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL,
    url             TEXT    NOT NULL,
    coverage        TEXT,                       -- Pass, Fail, Excluded
    crawled_as      TEXT,                       -- Googlebot desktop/mobile
    crawl_allowed   TEXT,                       -- Yes/No
    page_fetch      TEXT,                       -- Successful/Failed
    indexing        TEXT,                       -- Indexed/Not indexed
    last_crawl      TEXT,                       -- Date of last crawl
    created_at      TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sc_url_inspection_website ON sc_url_inspection(website_id);

-- Index Coverage data (imported from CSV export)
CREATE TABLE IF NOT EXISTS sc_coverage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL,
    status          TEXT    NOT NULL,           -- Error, Valid, Warning, Excluded
    category        TEXT    NOT NULL,           -- Specific issue type
    count           INTEGER NOT NULL DEFAULT 0, -- Number of affected URLs
    examples        TEXT,                       -- JSON array of sample URLs
    created_at      TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sc_coverage_website ON sc_coverage(website_id);

-- Links data (imported from CSV export)
CREATE TABLE IF NOT EXISTS sc_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id      INTEGER NOT NULL,
    target_page     TEXT    NOT NULL,           -- Your page URL
    source_page     TEXT    NOT NULL,           -- Linking page URL
    anchor_text     TEXT,                       -- Link text
    first_seen      TEXT,                       -- When link was first detected
    last_seen       TEXT,                       -- Most recent detection
    created_at      TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sc_links_website ON sc_links(website_id);
CREATE INDEX IF NOT EXISTS idx_sc_links_target ON sc_links(target_page);
