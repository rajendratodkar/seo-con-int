"""Pydantic schemas for the competitor analysis module."""
from pydantic import BaseModel, Field


class CompetitorCreate(BaseModel):
    website_id: int
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1)
    notes: str | None = None


class CompetitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None


class CompetitorOut(BaseModel):
    id: int
    website_id: int
    name: str
    url: str
    notes: str | None = None
    created_at: str
    updated_at: str


class RankingImport(BaseModel):
    competitor_id: int
    keyword: str = Field(min_length=1)
    position: float = Field(ge=0)
    url: str | None = None
    impressions: int | None = None
    source: str = Field(default="manual", pattern=r"^(manual|semrush|ahrefs|other)$")
    snapshot_date: str  # YYYY-MM-DD


class RankingBulkImport(BaseModel):
    competitor_id: int
    rankings: list[RankingImport] = Field(min_length=1, max_length=500)
    snapshot_date: str  # YYYY-MM-DD


class RankingOut(BaseModel):
    id: int
    competitor_id: int
    keyword: str
    normalized: str
    position: float
    url: str | None = None
    impressions: int | None = None
    source: str
    snapshot_date: str


class ContentGapOut(BaseModel):
    id: int
    website_id: int
    keyword: str
    competitor_id: int
    competitor_pos: float
    competitor_url: str | None = None
    our_position: float | None = None
    opportunity: str
    search_volume: int | None = None
    priority: float
    status: str
    created_at: str


class CompetitorSummary(BaseModel):
    competitor: CompetitorOut
    keyword_count: int
    avg_position: float | None = None
    top_keywords: list[dict]


class GapSummary(BaseModel):
    total_gaps: int
    new_content: int
    improve_existing: int
    quick_win: int
    top_gaps: list[ContentGapOut]
