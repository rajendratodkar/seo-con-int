"""YouTube metadata via oEmbed (no API key required)."""
import re

import httpx

from app.core.http import http_client

OEMBED_URL = "https://www.youtube.com/oembed"


def extract_video_id(url: str) -> str | None:
    patterns = (
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def fetch_metadata(url: str) -> dict | None:
    try:
        async with http_client(timeout=15.0) as client:
            response = await client.get(OEMBED_URL, params={"url": url, "format": "json"})
        if response.status_code != 200:
            return None
        data = response.json()
        return {
            "title": data.get("title"),
            "channel": data.get("author_name"),
            "channel_url": data.get("author_url"),
        }
    except httpx.HTTPError:
        return None
