"""Pydantic schemas for keyword clustering."""
from pydantic import BaseModel, Field


class ClusterCreate(BaseModel):
    website_id: int
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    pillar_keyword: str | None = None


class ClusterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    pillar_keyword: str | None = None


class ClusterKeywordAdd(BaseModel):
    keyword: str = Field(min_length=1)
    search_volume: int | None = None
    position: float | None = None


class ClusterOut(BaseModel):
    id: int
    website_id: int
    name: str
    description: str | None = None
    pillar_keyword: str | None = None
    keyword_count: int
    created_at: str
    updated_at: str


class ClusterDetail(ClusterOut):
    keywords: list[dict]


class AutoClusterRequest(BaseModel):
    website_id: int
    min_keywords_per_cluster: int = Field(default=2, ge=2, le=50)
    similarity_threshold: float = Field(default=0.3, ge=0.1, le=1.0)
