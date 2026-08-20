"""Pydantic schemas for backlink monitor."""
from pydantic import BaseModel, Field


class BacklinkCreate(BaseModel):
    website_id: int
    source_url: str = Field(min_length=1)
    target_url: str = Field(min_length=1)
    anchor_text: str | None = None
    is_nofollow: bool = False
    is_sponsored: bool = False
    domain_authority: int | None = Field(default=None, ge=0, le=100)
    page_authority: int | None = Field(default=None, ge=0, le=100)


class BacklinkImport(BaseModel):
    website_id: int
    backlinks: list[BacklinkCreate] = Field(min_length=1, max_length=1000)


class BacklinkUpdate(BaseModel):
    anchor_text: str | None = None
    is_nofollow: bool | None = None
    is_sponsored: bool | None = None
    domain_authority: int | None = Field(default=None, ge=0, le=100)
    page_authority: int | None = Field(default=None, ge=0, le=100)
    status: str | None = Field(default=None, pattern=r"^(active|lost|broken)$")


class BacklinkOut(BaseModel):
    id: int
    website_id: int
    source_url: str
    source_domain: str
    target_url: str
    anchor_text: str | None = None
    is_nofollow: bool
    is_sponsored: bool
    domain_authority: int | None = None
    page_authority: int | None = None
    status: str
    first_seen: str
    last_checked: str | None = None
    created_at: str
    updated_at: str


class BacklinkChangeOut(BaseModel):
    id: int
    website_id: int
    backlink_id: int | None = None
    change_type: str
    source_url: str
    target_url: str
    details: dict | None = None
    detected_at: str


class BacklinkProfile(BaseModel):
    total_links: int
    active_links: int
    lost_links: int
    broken_links: int
    unique_domains: int
    nofollow_count: int
    sponsored_count: int
    avg_domain_authority: float | None = None
    top_domains: list[dict]
    recent_changes: list[BacklinkChangeOut]
