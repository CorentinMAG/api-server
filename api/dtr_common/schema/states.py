from .base import StrictBaseModel
import datetime
from ..constantes import State as StateEnum, SubState


class StateSchema(StrictBaseModel):
    created_at: datetime.datetime
    failure_reason: str | None
    state: StateEnum
    sub_state: SubState | None
