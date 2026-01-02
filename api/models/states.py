from __future__ import annotations

from api.dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import BaseModel


class State(BaseModel, SerializerMixin):
    __tablename__ = "states"

    serialize_only = ("state", "created_at", "failure_reason", "sub_state")

    state: Mapped[StateEnum] = mapped_column(index=True)
    failure_reason: Mapped[str | None]
    sub_state: Mapped[SubStateEnum | None] = mapped_column(default=None, index=True)

    request_id: Mapped[int] = mapped_column(
        ForeignKey("transfer_requests.id", ondelete="CASCADE"), index=True
    )
