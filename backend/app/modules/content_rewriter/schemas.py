"""Pydantic schemas for content rewriter."""
from pydantic import BaseModel, Field


class RewriteRequest(BaseModel):
    website_id: int | None = None
    page_id: int | None = None
    content_type: str = Field(pattern=r"^(title|description|heading|custom)$")
    original_text: str = Field(min_length=1, max_length=1000)
    context: str | None = Field(default=None, max_length=500, description="Target keyword or page topic")
    num_variations: int = Field(default=3, ge=1, le=5)
    provider: str | None = Field(default=None, description="Override AI provider (uses default if not set)")


class RewriteOut(BaseModel):
    id: int
    website_id: int | None = None
    page_id: int | None = None
    content_type: str
    original_text: str
    context: str | None = None
    provider: str | None = None
    model: str | None = None
    rewrites: list[str]
    selected_index: int | None = None
    applied: bool
    created_at: str


class SelectRewrite(BaseModel):
    selected_index: int = Field(ge=0)
