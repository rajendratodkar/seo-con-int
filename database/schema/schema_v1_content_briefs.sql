-- Schema v1: AI Content Brief Generator
-- Stores data-driven writing briefs generated from keyword + SERP + competitor analysis

CREATE TABLE IF NOT EXISTS content_briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id INTEGER NOT NULL,
    target_keyword TEXT NOT NULL,
    primary_keyword TEXT NOT NULL,
    secondary_keywords TEXT,          -- JSON array
    search_intent TEXT,               -- informational, navigational, transactional, commercial
    target_word_count INTEGER,
    title_options TEXT,               -- JSON array of suggested titles
    meta_descriptions TEXT,           -- JSON array of suggested meta descriptions
    outline TEXT,                     -- JSON array of {heading, level, priority, notes}
    faq TEXT,                         -- JSON array of {question, answer}
    things_to_avoid TEXT,             -- JSON array of strings
    key_talking_points TEXT,          -- JSON array of strings
    serp_features TEXT,               -- JSON object — detected SERP features
    internal_links TEXT,              -- JSON array of {anchor, url, reason}
    source_evidence TEXT,             -- JSON object — SC data, clusters, competitors
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, finalized, sent_to_planner
    version INTEGER NOT NULL DEFAULT 1,
    markdown_export TEXT,             -- generated markdown for copy-paste
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS brief_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER NOT NULL,
    section_type TEXT NOT NULL,       -- competitor_insight, serp_feature, keyword_data, cluster_data
    title TEXT NOT NULL,
    content TEXT NOT NULL,            -- JSON section data
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (brief_id) REFERENCES content_briefs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS brief_competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    word_count INTEGER,
    headings TEXT,                    -- JSON array of heading strings
    keyword_density REAL,
    media_count INTEGER DEFAULT 0,
    has_faq INTEGER DEFAULT 0,
    has_schema INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (brief_id) REFERENCES content_briefs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_briefs_website ON content_briefs(website_id);
CREATE INDEX IF NOT EXISTS idx_content_briefs_keyword ON content_briefs(target_keyword);
CREATE INDEX IF NOT EXISTS idx_brief_sections_brief ON brief_sections(brief_id);
CREATE INDEX IF NOT EXISTS idx_brief_competitors_brief ON brief_competitors(brief_id);
