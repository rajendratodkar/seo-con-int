"""robots.txt compliance via urllib.robotparser."""
from urllib import robotparser
from urllib.parse import urlparse

import httpx

from app.core.http import http_client

USER_AGENT = "SEOContentIntelligenceBot"


class RobotsPolicy:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._parser = robotparser.RobotFileParser()
        self._loaded = False

    async def load(self) -> None:
        robots_url = self.base_url.rstrip("/") + "/robots.txt"
        try:
            async with http_client(timeout=10.0) as client:
                response = await client.get(robots_url)
            if response.status_code == 200:
                self._parser.parse(response.text.splitlines())
            # non-200 -> everything allowed
        except httpx.HTTPError:
            pass
        self._loaded = True

    def can_fetch(self, url: str) -> bool:
        if not self._loaded:
            return True
        try:
            return self._parser.can_fetch(USER_AGENT, url)
        except Exception:
            return True

    def same_site(self, url: str) -> bool:
        # Compare bare hosts so www/apex redirects (common on Astro/Netlify/
        # Vercel hosts) don't exclude every discovered link.
        return _bare_host(urlparse(url).netloc) == _bare_host(urlparse(self.base_url).netloc)


def _bare_host(netloc: str) -> str:
    host = netloc.split(":")[0].lower()
    return host[4:] if host.startswith("www.") else host
