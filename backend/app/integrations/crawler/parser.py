"""HTML extraction: everything the crawler records about a page (plan §6)."""
import json
from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup

SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}


@dataclass
class ParsedPage:
    url: str
    status_code: int
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    headings: list = field(default_factory=list)       # [{level, text}]
    text_content: str = ""
    word_count: int = 0
    links: list = field(default_factory=list)           # [{target_url, anchor_text, is_nofollow}]
    images: list = field(default_factory=list)          # [{src, alt}]
    schema_json: list = field(default_factory=list)     # JSON-LD blocks
    published_at: str | None = None
    modified_at: str | None = None


def parse_html(url: str, html: str, status_code: int) -> ParsedPage:
    soup = BeautifulSoup(html, "html.parser")
    page = ParsedPage(url=url, status_code=status_code)

    if soup.title and soup.title.string:
        page.title = soup.title.string.strip()

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        page.meta_description = meta_desc["content"].strip()

    canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
    if canonical and canonical.get("href"):
        page.canonical = urljoin(url, canonical["href"].strip())

    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            text = h.get_text(" ", strip=True)
            if text:
                page.headings.append({"level": level, "text": text[:300]})

    # Dates: meta properties first, then time tags
    page.published_at = _meta_date(soup, ("article:published_time", "datePublished"))
    page.modified_at = _meta_date(soup, ("article:modified_time", "dateModified"))
    if not page.published_at:
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag:
            page.published_at = time_tag["datetime"]

    # Links
    seen_links: set[str] = set()
    for a in soup.find_all("a", href=True):
        target = urljoin(url, a["href"].strip())
        if not target.startswith(("http://", "https://")) or target in seen_links:
            continue
        seen_links.add(target)
        rel = a.get("rel") or []
        page.links.append({
            "target_url": target,
            "anchor_text": a.get_text(" ", strip=True)[:200],
            "is_nofollow": "nofollow" in rel,
        })

    # Images
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        page.images.append({"src": urljoin(url, src), "alt": (img.get("alt") or "").strip()})

    # Structured data (JSON-LD)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            page.schema_json.append(json.loads(script.string or ""))
        except (json.JSONDecodeError, TypeError):
            continue

    # Visible text
    for tag in soup(SKIP_TEXT_TAGS):
        tag.decompose()
    body = soup.body or soup
    page.text_content = " ".join(body.get_text(" ", strip=True).split())
    page.word_count = len(page.text_content.split())
    return page


def _meta_date(soup: BeautifulSoup, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"itemprop": key})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None
