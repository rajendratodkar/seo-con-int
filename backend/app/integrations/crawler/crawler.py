"""Crawl orchestrator.

Seeds: sitemap URLs (if available) + homepage, then BFS over same-site links.
Respects robots.txt. Bounded by max_pages to stay a local, polite tool.
Fetches run on a small worker pool (bounded concurrency + per-request delay).
"""
import asyncio
import logging
from urllib.parse import urlparse

import httpx

from app.core.http import http_client

from app.integrations.crawler.parser import ParsedPage, parse_html
from app.integrations.crawler.robots import USER_AGENT, RobotsPolicy
from app.integrations.sitemap.sitemap import fetch_sitemap_urls

log = logging.getLogger(__name__)

DEFAULT_MAX_PAGES = 500
CRAWL_TIMEOUT = 20.0
CONCURRENCY = 3
POLITENESS_DELAY = 0.2


async def crawl_site(
    base_url: str,
    sitemap_url: str | None = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> list[ParsedPage]:
    robots = RobotsPolicy(base_url)
    await robots.load()

    queue: asyncio.Queue[str] = asyncio.Queue()
    seen: set[str] = set()

    def enqueue(url: str) -> None:
        normalized = _normalize(url)
        if normalized not in seen:
            seen.add(normalized)
            queue.put_nowait(url)

    if sitemap_url:
        for u in await fetch_sitemap_urls(sitemap_url, limit=max_pages):
            enqueue(u)
    enqueue(base_url)

    results: list[ParsedPage] = []
    failed: list[str] = []  # URLs that errored or were rate-limited (5xx)
    headers = {"User-Agent": f"{USER_AGENT}/0.1 (+local SEO audit)"}
    done = asyncio.Event()

    async with http_client(follow_redirects=True, timeout=CRAWL_TIMEOUT, headers=headers) as client:

        async def fetch_page(url: str) -> None:
            if not robots.same_site(url) or not robots.can_fetch(url):
                return
            try:
                response = await client.get(url)
            except httpx.HTTPError as exc:
                log.warning("crawl failed %s: %s", url, exc)
                failed.append(url)
                return

            content_type = response.headers.get("content-type", "")
            if "html" not in content_type:
                return
            if response.status_code >= 500:
                # Rate-limited or transient server error — retry once later.
                failed.append(url)
                return

            page = parse_html(str(response.url), response.text, response.status_code)
            results.append(page)
            if len(results) >= max_pages:
                done.set()

            # BFS: enqueue same-site html-ish links
            for link in page.links:
                target = link["target_url"]
                if robots.same_site(target) and _looks_html(target):
                    enqueue(target)

        async def worker() -> None:
            while not done.is_set():
                try:
                    url = await asyncio.wait_for(queue.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    if queue.empty():
                        return
                    continue
                try:
                    if len(results) >= max_pages:
                        continue
                    await fetch_page(url)
                finally:
                    queue.task_done()
                await asyncio.sleep(POLITENESS_DELAY)  # politeness delay

        await asyncio.gather(*(worker() for _ in range(CONCURRENCY)))

        # Retry pass: transient failures get one more try, gently.
        for url in failed:
            if len(results) >= max_pages:
                break
            await asyncio.sleep(POLITENESS_DELAY * 3)
            await fetch_page(url)

    log.info("crawl complete: %s -> %d pages", base_url, len(results))
    return results


def _normalize(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/') or '/'}"


def _looks_html(url: str) -> bool:
    path = urlparse(url).path.lower()
    return not path.endswith((".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".zip", ".css", ".js", ".xml"))
