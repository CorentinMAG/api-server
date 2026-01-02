from .base import StrictBaseModel


class WorkerCreate(StrictBaseModel):
    name: str
    queues: list[str]


class WorkerUpdate(StrictBaseModel):
    name: str | None = None
    queues: list[str] | None = None
