from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationItem(BaseModel):
    page: int
    page_size: int
    total: int


class Pagination(BaseModel, Generic[T]):
    # as a workaround, because sqlalchemy models are not regular Python classes. Later I will create TargetRead, ... models
    model_config = ConfigDict(arbitrary_types_allowed=True)
    pagination: PaginationItem
    items: list[T]
