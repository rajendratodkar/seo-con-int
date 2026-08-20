"""Redirect Manager schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RedirectType(int, Enum):
    PERMANENT_301 = 301
    TEMPORARY_302 = 302
    TEMPORARY_307 = 307
    PERMANENT_308 = 308


class RedirectCreate(BaseModel):
    website_id: int
    source_url: str = Field(..., min_length=1, description="Source URL to redirect from")
    target_url: str = Field(..., min_length=1, description="Target URL to redirect to")
    status_code: RedirectType = RedirectType.PERMANENT_301
    notes: Optional[str] = None


class RedirectUpdate(BaseModel):
    target_url: Optional[str] = None
    status_code: Optional[RedirectType] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RedirectResponse(BaseModel):
    id: int
    website_id: int
    source_url: str
    target_url: str
    status_code: int
    is_active: bool
    chain_depth: int
    hit_count: int
    last_checked_at: Optional[str] = None
    last_status_code: Optional[int] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class RedirectBulkImport(BaseModel):
    website_id: int
    redirects: list[dict]  # [{source, target, status_code?}]
    overwrite: bool = False  # Overwrite existing redirects for same source


class RedirectCheck(BaseModel):
    redirect_id: int
    checked_at: str
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    final_url: Optional[str] = None
    error_message: Optional[str] = None


class RedirectStats(BaseModel):
    total: int
    active: int
    inactive: int
    by_status_code: dict[str, int]
    chains_detected: int
    broken_count: int  # redirects pointing to 4xx/5xx
    avg_response_time_ms: Optional[float] = None
