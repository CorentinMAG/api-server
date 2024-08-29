from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
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
    nb_retry: Mapped[int] = mapped_column(default=0)
    next_retry_min_time: Mapped[str | None] = mapped_column(DateTime, default=None)

    last_state = column_property(
        select(State.state)
        .where(State.request_id == id)
        .order_by(State.created_at.desc())
        .limit(1)
        .correlate_except(State)
        .scalar_subquery()
    )

    last_sub_state = column_property(
        select(State.sub_state)
        .where(State.request_id == id)
        .order_by(State.created_at.desc())
        .limit(1)
        .correlate_except(State)
        .scalar_subquery()
    )

    failure_reason = column_property(
        select(State.failure_reason)
        .where(State.request_id == id)
        .order_by(State.created_at.desc())
        .limit(1)
        .correlate_except(State)
        .scalar_subquery()
    )


    state_created_at = column_property(
        select(State.created_at)
        .where(State.request_id == id)
        .order_by(State.created_at.asc())
        .limit(1)
        .correlate_except(State)
        .scalar_subquery()
    )