"""
Pagination schema for API endpoints.

This schema is used to define the parameters for pagination in API endpoints.
"""

from typing import Any

from pydantic import BaseModel


class PaginationParams(BaseModel):
    """Pagination parameters for API endpoints."""

    page: int = 1
    page_size: int = 10
    filters: dict[str, Any] | None = None
    search: str | None = None
    search_fields: list[str] | None = None
    sort_by: str | None = None
    sort_order: str = "asc"
