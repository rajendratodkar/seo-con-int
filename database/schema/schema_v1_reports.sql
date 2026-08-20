-- Schema v1: SEO Audit Reports
-- Stores generated reports and report templates

CREATE TABLE IF NOT EXISTS seo_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'full',  -- full, technical, content, performance
    format TEXT NOT NULL DEFAULT 'html',  -- html, pdf, json
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, generating, completed, failed
    period_days INTEGER NOT NULL DEFAULT 30,
    report_data TEXT,  -- JSON blob of all report sections
    file_path TEXT,  -- path to generated file
    generated_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    section_type TEXT NOT NULL,  -- overview, traffic, rankings, findings, audit, recommendations
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- JSON section data
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (report_id) REFERENCES seo_reports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_seo_reports_website ON seo_reports(website_id);
CREATE INDEX IF NOT EXISTS idx_report_sections_report ON report_sections(report_id);
