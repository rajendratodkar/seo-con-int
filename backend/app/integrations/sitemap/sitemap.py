"""Sitemap discovery and parsing (handles sitemap indexes)."""
import xml.etree.ElementTree as ET

import httpx

from app.core.http import http_client

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
MAX_SITEMAPS = 10
MAX_URLS = 5000


async def fetch_sitemap_urls(sitemap_url: str, limit: int = MAX_URLS) -> list[str]:
    """Return page URLs from a sitemap (following sitemap indexes one level)."""
    urls: list[str] = []
    sitemaps = [sitemap_url]
    seen_sitemaps: set[str] = set()

    async with http_client(follow_redirects=True, timeout=20.0) as client:
        while sitemaps and len(urls) < limit:
            current = sitemaps.pop(0)
            if current in seen_sitemaps or len(seen_sitemaps) >= MAX_SITEMAPS:
                continue
            seen_sitemaps.add(current)
            try:
                response = await client.get(current)
                if response.status_code != 200:
                    continue
                root = ET.fromstring(response.content)
            except (httpx.HTTPError, ET.ParseError):
                continue

            if root.tag == f"{SITEMAP_NS}sitemapindex":
                for sm in root.findall(f"{SITEMAP_NS}sitemap/{SITEMAP_NS}loc"):
                    if sm.text:
                        sitemaps.append(sm.text.strip())
            else:
                for url_el in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc"):
                    if url_el.text:
                        urls.append(url_el.text.strip())
                        if len(urls) >= limit:
                            break
    return urls
