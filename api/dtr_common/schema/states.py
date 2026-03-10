from __future__ import annotations

import datetime

from ..constantes import State as StateEnum, SubState
from .base import StrictBaseModel


class StateSchema(StrictBaseModel):
    created_at: datetime.datetime
    failure_reason: str | None
    state: StateEnum
    sub_state: SubState | None
