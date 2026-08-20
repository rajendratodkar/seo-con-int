"""Pydantic schemas for SEO checklist."""
from pydantic import BaseModel, Field


class ChecklistCreate(BaseModel):
    website_id: int
    page_id: int


class ChecklistItemAdd(BaseModel):
    category: str = Field(pattern=r"^(meta|content|technical|links|structured_data|performance)$")
    item_text: str = Field(min_length=1, max_length=500)
    notes: str | None = None


class ChecklistItemUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(todo|done|skipped|blocked)$")
    notes: str | None = None


class ChecklistItemOut(BaseModel):
    id: int
    checklist_id: int
    category: str
    item_text: str
    status: str
    finding_id: int | None = None
    notes: str | None = None
    completed_at: str | None = None
    created_at: str


class ChecklistOut(BaseModel):
    id: int
    website_id: int
    page_id: int
    status: str
    total_items: int
    done_items: int
    progress_pct: float
    created_at: str
    updated_at: str


class ChecklistDetail(ChecklistOut):
    items: list[ChecklistItemOut]
    page_url: str | None = None
    page_title: str | None = None
