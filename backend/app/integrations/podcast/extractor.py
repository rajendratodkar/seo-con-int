"""Podcast research extraction orchestrator.

Honest availability (plan §10): feed metadata is always kept; transcripts are
only recorded when a transcript URL is actually present.
"""
import json

import httpx

from app.core.http import http_client

from app.integrations.podcast.metadata import looks_like_feed, parse_feed


async def extract(feed_url: str) -> dict:
    """Returns {show_title, description, episodes, availability, raw}."""
    try:
        async with http_client(timeout=20.0) as client:
            response = await client.get(feed_url, follow_redirects=True)
        body = response.text
    except httpx.HTTPError:
        return {"availability": "pending", "error": "Feed unreachable"}

    if response.status_code != 200 or not looks_like_feed(body):
        return {"availability": "pending", "error": "URL is not a podcast feed"}

    feed = parse_feed(body)
    episodes = feed.get("episodes", [])
    with_transcript = sum(1 for e in episodes if e.get("transcript_url"))
    availability = "full" if with_transcript else "metadata_only"
    return {
        "show_title": feed.get("show_title"),
        "description": feed.get("description"),
        "episodes": episodes,
        "episode_count": len(episodes),
        "episodes_with_transcript": with_transcript,
        "availability": availability,
        "raw": json.dumps(feed, ensure_ascii=False),
    }
