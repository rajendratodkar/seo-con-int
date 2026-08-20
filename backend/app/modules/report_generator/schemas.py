"""Report Generator schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ReportType(str, Enum):
    FULL = "full"
    TECHNICAL = "technical"
    CONTENT = "content"
    PERFORMANCE = "performance"


class ReportFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportCreate(BaseModel):
    website_id: int
    title: str = Field(..., min_length=1, max_length=200)
    report_type: ReportType = ReportType.FULL
    format: ReportFormat = ReportFormat.HTML
    period_days: int = Field(30, ge=1, le=365)


class ReportResponse(BaseModel):
    id: int
    website_id: int
    title: str
    report_type: str
    format: str
    status: str
    period_days: int
    report_data: Optional[str] = None
    file_path: Optional[str] = None
    generated_at: Optional[str] = None
    created_at: str
    updated_at: str


class ReportSectionResponse(BaseModel):
    id: int
    report_id: int
    section_type: str
    title: str
    content: str
    sort_order: int
    created_at: str


class ReportSummary(BaseModel):
    id: int
    title: str
    report_type: str
    format: str
    status: str
    period_days: int
    generated_at: Optional[str] = None
    created_at: str
