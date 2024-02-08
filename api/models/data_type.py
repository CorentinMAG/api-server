from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer

class DataType(SQLBase):
    id: int | None = None
    logicalName: str
    description: str | None = None
    itemType: str
