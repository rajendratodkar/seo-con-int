"""Content Brief HTTP layer."""
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.api.dependencies import DbSession
from app.modules.content_brief.service import ContentBriefService
from app.modules.content_brief.schemas import BriefCreate, BriefUpdate

router = APIRouter()


@router.post("")
def create_brief(db: DbSession, data: BriefCreate):
    """Create and generate a content brief from keyword analysis."""
    return ContentBriefService(db).generate(data.website_id, data.target_keyword)


@router.get("")
def list_briefs(db: DbSession, website_id: int = Query(...)):
    """List all content briefs for a website."""
    return ContentBriefService(db).list_by_website(website_id)


@router.get("/{brief_id}")
def get_brief(db: DbSession, brief_id: int):
    """Get a specific content brief with all data."""
    return ContentBriefService(db).get(brief_id)


@router.put("/{brief_id}")
def update_brief(db: DbSession, brief_id: int, data: BriefUpdate):
    """Update a content brief."""
    fields = data.model_dump(exclude_unset=True)
    return ContentBriefService(db).update(brief_id, fields)


@router.delete("/{brief_id}")
def delete_brief(db: DbSession, brief_id: int):
    """Delete a content brief."""
    return ContentBriefService(db).delete(brief_id)


@router.get("/{brief_id}/sections")
def get_sections(db: DbSession, brief_id: int):
    """Get analysis sections for a brief."""
    return ContentBriefService(db).get_sections(brief_id)


@router.get("/{brief_id}/competitors")
def get_competitors(db: DbSession, brief_id: int):
    """Get competitor data for a brief."""
    return ContentBriefService(db).get_competitors(brief_id)


@router.get("/{brief_id}/export", response_class=PlainTextResponse)
def export_markdown(db: DbSession, brief_id: int):
    """Export brief as Markdown for copy-paste."""
    return ContentBriefService(db).export_markdown(brief_id)


@router.post("/{brief_id}/finalize")
def finalize_brief(db: DbSession, brief_id: int):
    """Mark brief as finalized."""
    return ContentBriefService(db).finalize(brief_id)


@router.post("/{brief_id}/send-to-planner")
def send_to_planner(db: DbSession, brief_id: int):
    """Mark brief as sent to article planner."""
    return ContentBriefService(db).send_to_planner(brief_id)
