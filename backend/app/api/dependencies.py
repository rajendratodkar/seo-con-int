"""Shared FastAPI dependencies (see docs/architecture/api-architecture.md)."""
from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_session

DbSession = Annotated[Session, Depends(get_session)]


class Pagination(BaseModel):
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=200, default=50)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def get_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Pagination:
    return Pagination(page=page, page_size=page_size)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]


def page_response(items: list, total: int, pagination: Pagination) -> dict:
    """Uniform list envelope used by every list endpoint."""
    return {"items": items, "total": total, "page": pagination.page, "page_size": pagination.page_size}
