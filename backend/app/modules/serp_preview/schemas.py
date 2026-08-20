"""SERP Preview schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class SERPPreviewRequest(BaseModel):
    """Request to generate a SERP preview."""
    title: str = Field(..., min_length=1, max_length=200, description="Page title")
    description: str = Field(..., min_length=1, max_length=500, description="Meta description")
    url: str = Field(..., min_length=1, description="Page URL")
    site_name: Optional[str] = Field(None, description="Site name (optional)")
    date: Optional[str] = Field(None, description="Publication date (optional)")


class SERPPreviewResponse(BaseModel):
    """SERP preview result."""
    title: str
    truncated_title: str
    title_length: int
    title_status: str  # good, warning, too_long
    description: str
    truncated_description: str
    description_length: int
    description_status: str  # good, warning, too_long, too_short
    url: str
    display_url: str
    site_name: Optional[str] = None
    date: Optional[str] = None


class PageMeta(BaseModel):
    """Page metadata for SERP preview."""
    page_id: int
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None


class SERPBulkPreviewRequest(BaseModel):
    """Bulk preview for multiple pages."""
    website_id: int
    page_ids: Optional[list[int]] = None  # Specific pages, or all if None
    limit: int = Field(50, ge=1, le=200)
