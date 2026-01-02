from .base import StrictBaseModel


class TriggerCreate(StrictBaseModel):
    name: str
    polling: int


class TriggerUpdate(StrictBaseModel):
    name: str | None = None
    polling: int | None = None
