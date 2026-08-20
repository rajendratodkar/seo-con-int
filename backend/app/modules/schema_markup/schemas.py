"""Pydantic schemas for schema markup builder."""
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    schema_type: str = Field(pattern=r"^(Article|FAQPage|HowTo|Product|BreadcrumbList|Organization)$")
    page_id: int | None = None
    params: dict = Field(default_factory=dict)


class ValidateRequest(BaseModel):
    json_ld: str  # Raw JSON-LD string to validate


class SaveSchemaRequest(BaseModel):
    page_id: int
    schema_type: str
    json_ld: str


class SchemaOut(BaseModel):
    id: int
    page_id: int
    schema_type: str
    json_ld: str
    validation_errors: str | None = None
    created_at: str
    updated_at: str
