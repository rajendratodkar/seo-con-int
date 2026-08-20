"""Content Brief schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class BriefCreate(BaseModel):
    website_id: int
    target_keyword: str = Field(..., min_length=1, max_length=200)
    primary_keyword: Optional[str] = None  # defaults to target_keyword
    secondary_keywords: Optional[list[str]] = None


class BriefUpdate(BaseModel):
    primary_keyword: Optional[str] = None
    secondary_keywords: Optional[list[str]] = None
    search_intent: Optional[str] = None
    target_word_count: Optional[int] = None
    title_options: Optional[list[str]] = None
    meta_descriptions: Optional[list[str]] = None
    outline: Optional[list[dict]] = None
    faq: Optional[list[dict]] = None
    things_to_avoid: Optional[list[str]] = None
    key_talking_points: Optional[list[str]] = None
    status: Optional[str] = None


class BriefOut(BaseModel):
    id: int
    website_id: int
    target_keyword: str
    primary_keyword: str
    secondary_keywords: Optional[list] = None
    search_intent: Optional[str] = None
    target_word_count: Optional[int] = None
    title_options: Optional[list] = None
    meta_descriptions: Optional[list] = None
    outline: Optional[list] = None
    faq: Optional[list] = None
    things_to_avoid: Optional[list] = None
    key_talking_points: Optional[list] = None
    serp_features: Optional[dict] = None
    internal_links: Optional[list] = None
    source_evidence: Optional[dict] = None
    status: str = "draft"
    version: int = 1
    markdown_export: Optional[str] = None
    created_at: str
    updated_at: str


class BriefSummary(BaseModel):
    id: int
    website_id: int
    target_keyword: str
    primary_keyword: str
    search_intent: Optional[str] = None
    target_word_count: Optional[int] = None
    status: str
    version: int
    created_at: str
    updated_at: str
