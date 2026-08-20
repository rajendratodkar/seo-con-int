"""Podcast RSS parsing — episode metadata and show notes."""
import xml.etree.ElementTree as ET

import httpx

from app.core.http import http_client

ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


def looks_like_feed(url: str) -> bool:
    lowered = url.lower()
    return lowered.endswith((".xml", ".rss")) or "/feed" in lowered or "/rss" in lowered


async def parse_feed(feed_url: str, max_episodes: int = 10) -> dict | None:
    try:
        async with http_client(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(feed_url)
        if response.status_code != 200:
            return None
        root = ET.fromstring(response.content)
    except (httpx.HTTPError, ET.ParseError):
        return None

    channel = root.find("channel")
    if channel is None:
        return None

    def _text(el, tag: str) -> str | None:
        node = el.find(tag)
        return node.text.strip() if node is not None and node.text else None

    episodes = []
    for item in channel.findall("item")[:max_episodes]:
        enclosure = item.find("enclosure")
        episodes.append({
            "title": _text(item, "title"),
            "description": (_text(item, "description") or "")[:2000],
            "link": _text(item, "link"),
            "published": _text(item, "pubDate"),
            "audio_url": enclosure.get("url") if enclosure is not None else None,
            "transcript_url": _text(item, f"{ITUNES_NS}transcript") or _text(item, "transcript"),
        })

    return {
        "show_title": _text(channel, "title"),
        "show_description": (_text(channel, "description") or "")[:500],
        "episodes": episodes,
    }
