"""Sitemap Generator HTTP layer."""
from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.dependencies import DbSession
from app.modules.sitemap_generator.schemas import SitemapSettingsUpdate, SitemapOverrideCreate
from app.modules.sitemap_generator.service import SitemapGeneratorService

router = APIRouter()


def _svc(db: DbSession) -> SitemapGeneratorService:
    return SitemapGeneratorService(db)


@router.get("/settings")
def get_settings(db: DbSession, website_id: int = Query(...)):
    """Get sitemap settings for a website."""
    return _svc(db).get_settings(website_id)


@router.put("/settings")
def update_settings(payload: SitemapSettingsUpdate, db: DbSession, website_id: int = Query(...)):
    """Update sitemap settings."""
    return _svc(db).update_settings(website_id, **payload.model_dump(exclude_none=True))


@router.get("/overrides")
def list_overrides(db: DbSession, website_id: int = Query(...)):
    """List URL pattern overrides."""
    return _svc(db).list_overrides(website_id)


@router.post("/overrides", status_code=201)
def add_override(payload: SitemapOverrideCreate, db: DbSession):
    """Add a URL pattern override."""
    return _svc(db).add_override(
        payload.website_id, payload.url_pattern,
        payload.priority, payload.changefreq, payload.include,
    )


@router.delete("/overrides/{override_id}")
def delete_override(override_id: int, db: DbSession):
    """Delete a URL pattern override."""
    return _svc(db).delete_override(override_id)


@router.get("/generate")
def generate_sitemap(db: DbSession, website_id: int = Query(...)):
    """Generate and return XML sitemap."""
    result = _svc(db).generate(website_id)
    return Response(content=result["xml"], media_type="application/xml")


@router.get("/preview")
def preview_sitemap(db: DbSession, website_id: int = Query(...)):
    """Preview sitemap stats without returning full XML."""
    result = _svc(db).generate(website_id)
    return {
        "url_count": result["url_count"],
        "excluded_count": result["excluded_count"],
        "total_pages": result["total_pages"],
        "xml_preview": result["xml"][:2000] + "..." if len(result["xml"]) > 2000 else result["xml"],
    }
