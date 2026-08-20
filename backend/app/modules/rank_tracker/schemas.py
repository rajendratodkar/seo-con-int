"""Rank Tracker schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class TrackedKeywordCreate(BaseModel):
    website_id: int
    keyword: str = Field(..., min_length=1, max_length=200)
    target_url: Optional[str] = None
    group_name: Optional[str] = None
    notes: Optional[str] = None


class TrackedKeywordUpdate(BaseModel):
    target_url: Optional[str] = None
    group_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TrackedKeywordResponse(BaseModel):
    id: int
    website_id: int
    keyword: str
    target_url: Optional[str] = None
    group_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    current_position: Optional[int] = None
    previous_position: Optional[int] = None
    position_change: Optional[int] = None
    best_position: Optional[int] = None
    worst_position: Optional[int] = None
    avg_position: Optional[float] = None
    created_at: str
    updated_at: str


class RankSnapshotCreate(BaseModel):
    keyword_id: int
    position: Optional[int] = None
    search_volume: Optional[int] = None
    clicks: Optional[int] = None
    impressions: Optional[int] = None
    ctr: Optional[float] = None
    url: Optional[str] = None
    search_engine: str = "google"
    country: str = "us"
    device: str = "desktop"
    snapshot_date: str


class RankSnapshotResponse(BaseModel):
    id: int
    keyword_id: int
    position: Optional[int] = None
    previous_position: Optional[int] = None
    change: Optional[int] = None
    search_volume: Optional[int] = None
    clicks: Optional[int] = None
    impressions: Optional[int] = None
    ctr: Optional[float] = None
    url: Optional[str] = None
    search_engine: str
    country: str
    device: str
    snapshot_date: str
    created_at: str


class RankAlertResponse(BaseModel):
    id: int
    keyword_id: int
    alert_type: str
    old_position: Optional[int] = None
    new_position: Optional[int] = None
    change: Optional[int] = None
    message: str
    is_read: bool
    created_at: str


class RankTrackerStats(BaseModel):
    total_keywords: int
    active_keywords: int
    avg_position: Optional[float] = None
    top_10_count: int
    top_20_count: int
    top_50_count: int
    position_improved: int
    position_dropped: int
    position_unchanged: int
    best_keyword: Optional[str] = None
    best_position: Optional[int] = None


class KeywordTrend(BaseModel):
    keyword_id: int
    keyword: str
    current_position: Optional[int] = None
    trend: str  # improving, declining, stable
    data_points: list[dict]  # [{date, position}]
