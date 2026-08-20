"""SEO analyzer — the single owner of page-level SEO analysis (Rule 2).

Pure computation: takes crawled data, returns findings. No DB access here.
"""
from app.engines.seo.content import check_content
from app.engines.seo.links import check_links
from app.engines.seo.metadata import check_metadata
from app.engines.seo.scoring import score_page
from app.engines.seo.structured_data import check_structured_data
from app.engines.seo.technical import check_images


def analyze_page(page: dict, content: dict | None, links: list[dict], all_page_urls: set[str]) -> dict:
    findings: list[dict] = []
    findings += check_metadata(page, content)
    findings += check_content(page, content)
    findings += check_images(page, content)
    findings += check_structured_data(page, content)
    findings += check_links(page, links, all_page_urls)
    return {"page_id": page["id"], "findings": findings, "score": score_page(findings)}
