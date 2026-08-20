"""Pydantic schemas for page speed insights."""
from pydantic import BaseModel, Field


class PageSpeedCheck(BaseModel):
    website_id: int
    page_id: int
    url: str
    lcp: float | None = Field(default=None, ge=0)
    fid: float | None = Field(default=None, ge=0)
    cls: float | None = Field(default=None, ge=0)
    fcp: float | None = Field(default=None, ge=0)
    ttfb: float | None = Field(default=None, ge=0)
    tti: float | None = Field(default=None, ge=0)
    performance_score: int | None = Field(default=None, ge=0, le=100)
    accessibility_score: int | None = Field(default=None, ge=0, le=100)
    best_practices_score: int | None = Field(default=None, ge=0, le=100)
    seo_score: int | None = Field(default=None, ge=0, le=100)
    opportunities: list[dict] | None = None
    diagnostics: list[dict] | None = None
    source: str = Field(default="manual", pattern=r"^(manual|pagespeed_api|lighthouse)$")


class PageSpeedSnapshotOut(BaseModel):
    id: int
    website_id: int
    page_id: int
    url: str
    lcp: float | None = None
    fid: float | None = None
    cls: float | None = None
    fcp: float | None = None
    ttfb: float | None = None
    tti: float | None = None
    performance_score: int | None = None
    accessibility_score: int | None = None
    best_practices_score: int | None = None
    seo_score: int | None = None
    opportunities: list[dict] | None = None
    diagnostics: list[dict] | None = None
    source: str
    checked_at: str
    created_at: str
