from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from dtr_common.constantes import State as StateEnum

from ..db import Base as SQLBase
from .states import State

if TYPE_CHECKING:
    from .policies import TransferPolicy


class TransferRequest(SQLBase, SerializerMixin):
    __tablename__ = "transfer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    size: Mapped[int | None]
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    states: Mapped[list[State]] = relationship()
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("transfer_policies.id", ondelete="SET NULL"))
    policy: Mapped[TransferPolicy] = relationship(back_populates="transfers")
    created_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)

    last_state = column_property(
        select(State.state)
        .where(State.request_id == id)
        .order_by(State.created_at.desc())
        .limit(1)
        .correlate_except(State)
        .scalar_subquery()
    )

    nb_retry = column_property(
        select(func.count(State.id))
        .where(State.request_id == id)
        .where(State.state == StateEnum.FAILED)
        .correlate_except(State)
        .scalar_subquery()
    )

    reason = column_property(
        select(State.reason)
        .where(State.request_id == id)
        .order_by(State.created_at.desc())
        .limit(1)
        .correlate_except(State)
        .scalar_subquery()
    )
