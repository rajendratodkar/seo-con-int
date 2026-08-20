"""Pydantic schemas for sitemap generator."""
from pydantic import BaseModel, Field


class SitemapSettingsUpdate(BaseModel):
    default_priority: float = Field(default=0.5, ge=0, le=1)
    default_changefreq: str = Field(default="weekly", pattern=r"^(always|hourly|daily|weekly|monthly|yearly|never)$")
    include_images: bool = True
    include_news: bool = False
    max_urls: int = Field(default=50000, ge=1, le=500000)
    exclude_patterns: list[str] | None = None


class SitemapOverrideCreate(BaseModel):
    website_id: int
    url_pattern: str = Field(min_length=1)
    priority: float | None = Field(default=None, ge=0, le=1)
    changefreq: str | None = Field(default=None, pattern=r"^(always|hourly|daily|weekly|monthly|yearly|never)$")
    include: bool = True


class SitemapOverrideOut(BaseModel):
    id: int
    website_id: int
    url_pattern: str
    priority: float | None = None
    changefreq: str | None = None
    include: bool
    created_at: str
