from __future__ import annotations

import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum

from ..db import Base as SQLBase


class State(SQLBase, SerializerMixin):
    __tablename__ = "states"

    serialize_only = ("state", "created_at", "failure_reason", "sub_state", "id")

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[StateEnum]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    request_id: Mapped[int] = mapped_column(ForeignKey("transfer_requests.id", ondelete="CASCADE"))
    failure_reason: Mapped[str | None]
    sub_state: Mapped[SubStateEnum | None] = mapped_column(default=None)
