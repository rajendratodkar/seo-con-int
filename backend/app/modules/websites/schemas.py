"""Pydantic schemas for the websites module."""
from pydantic import BaseModel, Field


class WebsiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=4)
    sitemap_url: str | None = None


class WebsiteUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    sitemap_url: str | None = None
    status: str | None = None


class WebsiteOut(BaseModel):
    id: int
    name: str
    url: str
    platform: str
    sitemap_url: str | None
    status: str
    created_at: str
    updated_at: str


class DetectionResult(BaseModel):
    platform: str
    sitemap_url: str | None
    reachable: bool
    status_code: int | None = None


class CrawlJobOut(BaseModel):
    job_id: int
    status: str
