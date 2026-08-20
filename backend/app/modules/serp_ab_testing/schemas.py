"""SERP A/B Testing schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestVariant(str, Enum):
    CONTROL = "control"
    VARIANT = "variant"


class SERPTestCreate(BaseModel):
    website_id: int
    page_id: int
    name: str = Field(..., min_length=1, max_length=200)
    # Control (original)
    control_title: str = Field(..., min_length=1, max_length=200)
    control_description: str = Field(..., min_length=1, max_length=500)
    # Variant (new)
    variant_title: str = Field(..., min_length=1, max_length=200)
    variant_description: str = Field(..., min_length=1, max_length=500)
    # Settings
    min_duration_days: int = Field(7, ge=1, le=90)
    confidence_level: float = Field(0.95, ge=0.80, le=0.99)


class SERPTestUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TestStatus] = None
    min_duration_days: Optional[int] = None
    confidence_level: Optional[float] = None


class SERPTestResponse(BaseModel):
    id: int
    website_id: int
    page_id: int
    name: str
    status: str
    # Control
    control_title: str
    control_description: str
    control_clicks: int
    control_impressions: int
    control_ctr: float
    control_avg_position: float
    # Variant
    variant_title: str
    variant_description: str
    variant_clicks: int
    variant_impressions: int
    variant_ctr: float
    variant_avg_position: float
    # Results
    winner: Optional[str] = None  # control, variant, inconclusive
    confidence: Optional[float] = None
    z_score: Optional[float] = None
    p_value: Optional[float] = None
    lift: Optional[float] = None  # CTR improvement percentage
    # Settings
    min_duration_days: int
    confidence_level: float
    # Dates
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str


class SERPTestSnapshot(BaseModel):
    id: int
    test_id: int
    variant: str  # control, variant
    snapshot_date: str
    clicks: int
    impressions: int
    ctr: float
    avg_position: float
    created_at: str


class SERPTestStats(BaseModel):
    total_tests: int
    running: int
    completed: int
    control_wins: int
    variant_wins: int
    inconclusive: int
    avg_lift: Optional[float] = None


class SERPTestResult(BaseModel):
    test_id: int
    winner: str
    confidence: float
    z_score: float
    p_value: float
    control_ctr: float
    variant_ctr: float
    lift: float
    is_significant: bool
    recommendation: str
