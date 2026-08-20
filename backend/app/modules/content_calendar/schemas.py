"""Pydantic schemas for content calendar."""
from pydantic import BaseModel, Field


class CalendarEventCreate(BaseModel):
    website_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    event_type: str = Field(default="article", pattern=r"^(article|review|publish|meeting|deadline)$")
    start_date: str  # YYYY-MM-DD
    end_date: str | None = None
    plan_id: int | None = None
    draft_id: int | None = None
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|urgent)$")
    color: str | None = None
    assignee: str | None = None
    notes: str | None = None


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    event_type: str | None = Field(default=None, pattern=r"^(article|review|publish|meeting|deadline)$")
    status: str | None = Field(default=None, pattern=r"^(planned|in_progress|review|published|overdue|cancelled)$")
    start_date: str | None = None
    end_date: str | None = None
    priority: str | None = Field(default=None, pattern=r"^(low|normal|high|urgent)$")
    color: str | None = None
    assignee: str | None = None
    notes: str | None = None


class CalendarEventOut(BaseModel):
    id: int
    website_id: int
    title: str
    description: str | None = None
    event_type: str
    status: str
    start_date: str
    end_date: str | None = None
    plan_id: int | None = None
    draft_id: int | None = None
    priority: str
    color: str | None = None
    assignee: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str
