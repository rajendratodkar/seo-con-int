"""Search Console File Upload schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class ScUploadCreate(BaseModel):
    """Schema for file upload request."""
    website_id: int
    import_type: str = Field("performance", pattern="^(performance|url_inspection|coverage|links)$")


class ScUploadResult(BaseModel):
    """Schema for upload result response."""
    id: int
    website_id: int
    filename: str
    file_type: str
    import_type: str
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_errors: int
    error_details: Optional[list[dict]] = None
    status: str
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class ScImportSummary(BaseModel):
    """Schema for import summary."""
    import_id: int
    rows_imported: int
    rows_skipped: int
    rows_errors: int
    error_count: int
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    message: str
