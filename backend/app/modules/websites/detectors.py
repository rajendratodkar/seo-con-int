"""Platform and sitemap detection heuristics."""
import httpx

from app.core.http import http_client

SITEMAP_CANDIDATES = (
    "/sitemap.xml",
    "/sitemap-index.xml",  # Astro (@astrojs/sitemap) default index name
    "/sitemap_index.xml",
    "/sitemap-0.xml",  # Astro single-sitemap output
    "/sitemap.xml.gz",
    "/wp-sitemap.xml",
    "/sitemap/sitemap.xml",
)

UA = "Mozilla/5.0 (compatible; SEOContentIntelligence/0.1)"


async def fetch(url: str, timeout: float = 15.0) -> httpx.Response | None:
    try:
        async with http_client(follow_redirects=True, timeout=timeout, headers={"User-Agent": UA}) as client:
            return await client.get(url)
    except httpx.HTTPError:
        return None


def detect_platform_from_html(html: str, headers: dict) -> str:
    lowered = html.lower()
    header_text = " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
    if "wp-content" in lowered or "wp-includes" in lowered or "wp-json" in lowered:
        return "wordpress"
    if 'name="generator" content="wordpress' in lowered:
        return "wordpress"
    if "x-powered-by: wp engine" in header_text or "wp engine" in header_text:
        return "wordpress"
    if 'name="generator" content="astro' in lowered:
        return "astro"
    if "astro/islands" in lowered or "__astro" in lowered:
        return "astro"
    if 'name="generator" content="next.js' in lowered:
        return "static"
    return "unknown"


async def detect_sitemap(base_url: str) -> str | None:
    # 1. robots.txt "Sitemap:" directive is authoritative when present.
    robots = await fetch(base_url.rstrip("/") + "/robots.txt", timeout=10.0)
    if robots is not None and robots.status_code == 200:
        for line in robots.text.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                candidate = line.split(":", 1)[1].strip()
                if candidate.startswith("http") and await _looks_like_sitemap(candidate):
                    return candidate
    # 2. Well-known paths (incl. Astro's sitemap-index.xml).
    for path in SITEMAP_CANDIDATES:
        url = base_url.rstrip("/") + path
        if await _looks_like_sitemap(url):
            return url
    return None


async def _looks_like_sitemap(url: str) -> bool:
    response = await fetch(url, timeout=10.0)
    return (
        response is not None
        and response.status_code == 200
        and "<" in response.text[:500]
    )


async def test_website(url: str) -> tuple[bool, int | None]:
    response = await fetch(url)
    if response is None:
        return False, None
    return response.status_code < 400, response.status_code
