"""Pydantic schemas for the bulk operations module."""
from pydantic import BaseModel, Field


class BulkCrawlRequest(BaseModel):
    """Request to crawl multiple websites at once."""
    website_ids: list[int] = Field(min_length=1, max_length=50)
    max_pages_per_site: int = Field(default=50, ge=1, le=500)


class BulkAnalyzeRequest(BaseModel):
    """Request to run SEO analysis on multiple pages at once."""
    website_ids: list[int] = Field(min_length=1, max_length=50)
    page_limit: int = Field(default=100, ge=1, le=1000)


class BulkIdeaRequest(BaseModel):
    """Request to generate content ideas from multiple sources at once."""
    website_ids: list[int] = Field(min_length=1, max_length=50)
    sources: list[str] = Field(
        default=["search_console"],
        description="Sources to generate ideas from: search_console, youtube, manual"
    )


class BulkJobOut(BaseModel):
    """Response for a bulk operation job."""
    job_id: int
    status: str
    operation: str
    total_items: int


class BulkJobStatus(BaseModel):
    """Detailed status of a bulk operation."""
    job_id: int
    operation: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    created_at: str
    finished_at: str | None = None
    error_message: str | None = None
