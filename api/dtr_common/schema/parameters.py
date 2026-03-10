from __future__ import annotations

from ..constantes import Mode
from .base import StrictBaseModel


class GlobalParametersCreate(StrictBaseModel):
    mode: Mode = Mode.ONLINE
    tmp_prefix: str | None = None
    final_prefix: str | None = None
    retry_delay: int = 300
    max_retry: int = 5
    transfer_requests_history: int = 30
    only_new_data: bool = True
    transfer_timeout: int = 3600
    queue_timeout: int = 3600
    polling_interval: int = 30
    queue_limit: int = 100
    queue_threshold: int = 80


class GlobalParametersUpdate(StrictBaseModel):
    mode: Mode | None = None
    tmp_prefix: str | None = None
    final_prefix: str | None = None
    retry_delay: int | None = None
    max_retry: int | None = None
    transfer_requests_history: int | None = None
    only_new_data: bool | None = None
    transfer_timeout: int | None = None
    queue_timeout: int | None = None
    polling_interval: int | None = None
    queue_limit: int | None = None
    queue_threshold: int | None = None
