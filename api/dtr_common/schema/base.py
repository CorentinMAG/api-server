from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class TimestampMixin(StrictBaseModel):
    created_at: datetime
    updated_at: datetime | None = None


class IDMixin(StrictBaseModel):
    id: int
