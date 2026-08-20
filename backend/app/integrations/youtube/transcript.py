"""Best-effort YouTube transcript retrieval.

Availability is recorded honestly: if nothing can be fetched, the source is
marked metadata_only — we NEVER pretend content was analyzed (plan §9).
"""
import httpx

from app.core.http import http_client


async def try_fetch_transcript(video_id: str) -> str | None:
    for lang in ("en", "hi"):
        url = "https://video.google.com/timedtext"
        try:
            async with http_client(timeout=15.0) as client:
                response = await client.get(url, params={"lang": lang, "v": video_id})
            if response.status_code == 200 and response.text.strip():
                # Strip XML tags to plain text
                import re

                text = re.sub(r"<[^>]+>", " ", response.text)
                text = " ".join(text.split())
                if len(text) > 50:
                    return text
        except httpx.HTTPError:
            continue
    return None
