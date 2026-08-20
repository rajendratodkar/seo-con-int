"""Idempotent seed data: official reference documents and starter SEO rules.

Rule: references and rules stay in separate tables (Rule -> Reference -> Official document).
"""
import logging

from sqlalchemy import text

from app.database.connection import get_engine

log = logging.getLogger(__name__)

REFERENCE_SEEDS = [
    ("google_seo", "Google Search Central — SEO Starter Guide", "https://developers.google.com/search/docs/fundamentals/seo-starter-guide"),
    ("google_seo", "Google Search Central — How Search Works", "https://developers.google.com/search/docs/fundamentals/how-search-works"),
    ("google_search_console", "Google Search Console Help", "https://support.google.com/webmasters/"),
    ("google_search_console", "Search Console API Documentation", "https://developers.google.com/webmaster-tools"),
    ("google_structured_data", "Google Structured Data Documentation", "https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"),
    ("google_spam_policies", "Google Spam Policies", "https://developers.google.com/search/docs/essentials/spam-policies"),
    ("sebi", "SEBI Official Website", "https://www.sebi.gov.in/"),
    ("amfi", "AMFI Official Website", "https://www.amfiindia.com/"),
    ("rbi", "RBI Official Website", "https://www.rbi.org.in/"),
    ("income_tax", "Income Tax Department of India", "https://www.incometax.gov.in/"),
    ("amc", "AMC Disclosure Standards", ""),
    ("other_official", "Official Regulatory Documents Registry", ""),
]

RULE_SEEDS = [
    ("META-001", "Title tag present and sized", "Every page must have a single unique title tag roughly 30-60 characters.", "technical", "warning", "Google SEO"),
    ("META-002", "Meta description present", "Pages should carry a meta description summarizing content.", "technical", "info", "Google SEO"),
    ("META-003", "Canonical tag consistency", "Canonical URL must exist and not conflict with sitemap.", "technical", "warning", "Google SEO"),
    ("H-001", "Single H1 per page", "Pages should contain exactly one H1 heading.", "technical", "info", "Google SEO"),
    ("IMG-001", "Images carry ALT text", "Content images should have descriptive ALT attributes.", "technical", "info", "Google SEO"),
    ("SD-001", "Structured data validity", "JSON-LD structured data must be valid for its declared type.", "technical", "warning", "Google Structured Data"),
    ("CNT-001", "Thin content detection", "Pages below a reasonable word count may be flagged thin.", "content", "warning", "Google SEO"),
    ("CNT-002", "Content freshness", "Financial content older than a threshold should be reviewed.", "content", "info", "Google SEO"),
    ("LNK-001", "Broken internal links", "Internal links must resolve to a live page.", "technical", "critical", "Google SEO"),
    ("FIN-001", "Regulatory disclaimer present", "Financial advice content must carry applicable disclaimers (SEBI/RBI context).", "financial", "critical", "SEBI"),
    ("SPM-001", "No keyword stuffing", "Content must avoid unnatural keyword repetition.", "content", "warning", "Google Spam Policies"),
]


def run_seeds() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        # References (category + title is unique)
        for category, title, url in REFERENCE_SEEDS:
            conn.execute(
                text(
                    "INSERT INTO reference_docs (category, title, url) "
                    "VALUES (:category, :title, :url) "
                    "ON CONFLICT (category, title) DO NOTHING"
                ),
                {"category": category, "title": title, "url": url},
            )

        # Rules linked to their reference document (by category's first document)
        category_ref = {
            "Google SEO": "google_seo",
            "Google Structured Data": "google_structured_data",
            "Google Spam Policies": "google_spam_policies",
            "SEBI": "sebi",
        }
        ref_ids = {
            row.category: row.id
            for row in conn.execute(
                text("SELECT category, MIN(id) AS id FROM reference_docs GROUP BY category")
            ).fetchall()
        }
        for rule_code, name, description, category, severity, ref_title in RULE_SEEDS:
            conn.execute(
                text(
                    "INSERT INTO seo_rules (rule_code, name, description, category, severity, reference_id) "
                    "VALUES (:rule_code, :name, :description, :category, :severity, :reference_id) "
                    "ON CONFLICT (rule_code) DO NOTHING"
                ),
                {
                    "rule_code": rule_code,
                    "name": name,
                    "description": description,
                    "category": category,
                    "severity": severity,
                    "reference_id": ref_ids.get(category_ref.get(ref_title, "")),
                },
            )
    log.info("Seed data verified (references + rules)")
