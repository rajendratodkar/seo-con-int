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
