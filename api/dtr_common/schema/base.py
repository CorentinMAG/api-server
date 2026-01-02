from pydantic import BaseModel, ConfigDict
from datetime import datetime


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class TimestampMixin(StrictBaseModel):
    created_at: datetime
    updated_at: datetime | None = None


class IDMixin(StrictBaseModel):
    id: int
