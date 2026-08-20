"""YouTube research extraction orchestrator."""
import json

from app.integrations.youtube.metadata import extract_video_id, fetch_metadata
from app.integrations.youtube.transcript import try_fetch_transcript


async def extract(url: str) -> dict:
    """Returns {title, channel, video_id, transcript, availability, raw}."""
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL", "availability": "pending"}

    metadata = await fetch_metadata(url)
    if metadata is None:
        return {"video_id": video_id, "availability": "pending", "error": "Metadata unavailable"}

    transcript = await try_fetch_transcript(video_id)
    availability = "full" if transcript else "metadata_only"
    return {
        "video_id": video_id,
        "title": metadata.get("title"),
        "channel": metadata.get("channel"),
        "transcript": transcript,
        "availability": availability,
        "raw": json.dumps({"video_id": video_id, **metadata}),
    }
