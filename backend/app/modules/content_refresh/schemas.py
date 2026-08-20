"""Content Refresh schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class RefreshRuleCreate(BaseModel):
    website_id: int
    name: str = Field(..., min_length=1, max_length=100)
    min_age_days: int = Field(90, ge=7, le=365)
    traffic_drop_pct: float = Field(10.0, ge=0, le=100)
    staleness_weight: float = Field(1.0, ge=0, le=2)
    traffic_weight: float = Field(1.0, ge=0, le=2)


class RefreshRuleUpdate(BaseModel):
    name: Optional[str] = None
    min_age_days: Optional[int] = None
    traffic_drop_pct: Optional[float] = None
    staleness_weight: Optional[float] = None
    traffic_weight: Optional[float] = None
    enabled: Optional[bool] = None


class RefreshRuleOut(BaseModel):
    id: int
    website_id: int
    name: str
    min_age_days: int
    traffic_drop_pct: float
    staleness_weight: float
    traffic_weight: float
    enabled: int
    created_at: str
    updated_at: str


class RefreshScheduleOut(BaseModel):
    id: int
    website_id: int
    page_id: int
    rule_id: Optional[int] = None
    priority_score: float
    priority_date: Optional[str] = None
    reason: Optional[str] = None
    suggested_changes: Optional[list] = None
    status: str
    created_at: str
    updated_at: str


class RefreshHistoryOut(BaseModel):
    id: int
    schedule_id: int
    page_id: int
    action: str
    changes_made: Optional[str] = None
    clicks_before: Optional[int] = None
    clicks_after: Optional[int] = None
    impressions_before: Optional[int] = None
    impressions_after: Optional[int] = None
    position_before: Optional[float] = None
    position_after: Optional[float] = None
    notes: Optional[str] = None
    created_at: str


class ScanResult(BaseModel):
    pages_scanned: int
    stale_pages_found: int
    schedules_created: int
    recommendations: list[dict]
