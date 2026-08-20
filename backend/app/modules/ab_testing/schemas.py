"""Pydantic schemas for the A/B testing module."""
from pydantic import BaseModel, Field


class ABTestCreate(BaseModel):
    website_id: int
    page_id: int
    name: str = Field(min_length=1, max_length=200)
    element: str = Field(default="title", pattern=r"^(title|description|both)$")
    control_title: str | None = None
    control_description: str | None = None
    variant_title: str | None = None
    variant_description: str | None = None
    min_duration_days: int = Field(default=7, ge=1, le=90)


class ABTestUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    min_duration_days: int | None = Field(default=None, ge=1, le=90)


class ABTestOut(BaseModel):
    id: int
    website_id: int
    page_id: int
    name: str
    element: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    min_duration_days: int
    winner: str | None = None
    confidence: float | None = None
    result_summary: dict | None = None
    created_at: str
    updated_at: str


class ABVariantOut(BaseModel):
    id: int
    test_id: int
    variant_type: str
    title: str | None = None
    description: str | None = None


class ABTestDetail(ABTestOut):
    control: ABVariantOut | None = None
    variant: ABVariantOut | None = None


class ABTestStartRequest(BaseModel):
    test_id: int


class ABTestCompleteRequest(BaseModel):
    test_id: int
