from __future__ import annotations

from .base import StrictBaseModel


class QueueCreate(StrictBaseModel):
    name: str
    priority: int = 1
    timeout: int = 300
    limit: int = 100
    threshold: int = 80


class QueueUpdate(StrictBaseModel):
    name: str | None = None
    priority: int | None = None
    timeout: int | None = None
    limit: int | None = None
    thresold: int | None = None
