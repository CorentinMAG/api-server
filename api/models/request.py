from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base
from .states import State

if TYPE_CHECKING:
    from .policies import DestinationPolicy, TransferPolicy


class TransferRequest(Base, SerializerMixin):
    __tablename__ = "transfer_requests"

    serialize_only = (
        "id",
        "filename",
        "size",
        "uid",
        "multi_dest_uid",
        "dest",
        "src_relative_path"
    )

    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True, nullable=False, index=True)

    # This uid is the same for all transfer requests created when multi destinations is involved
    multi_dest_uid: Mapped[uuid.UUID | None] = mapped_column(index=True)
    filename: Mapped[str] = mapped_column(nullable=False, index=True)
    size: Mapped[int | None] = mapped_column(BigInteger, default=None, index=True)  # in Bytes
    follows_from_task: Mapped[uuid.UUID | None] = mapped_column(default=None)
    src_relative_path: Mapped[str | None]

    # transfer metrics
    nb_retry: Mapped[int] = mapped_column(default=0)
    next_retry_min_time: Mapped[str | None] = mapped_column(DateTime, default=None, index=True)
    start: Mapped[str | None] = mapped_column(DateTime, default=None)
    end: Mapped[str | None] = mapped_column(DateTime, default=None)
    download_rate: Mapped[float | None]
    download_time: Mapped[float | None]
    upload_rate: Mapped[float | None]
    upload_time: Mapped[float | None]
    
    # denormalized current state for efficient querying
    current_state_id: Mapped[int | None] = mapped_column(ForeignKey("states.id", ondelete="SET NULL"))

    # foreign keys
    dest_id: Mapped[int | None] = mapped_column(ForeignKey("destination_policies.id", ondelete="SET NULL"))
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("transfer_policies.id", ondelete="SET NULL"))
    
    # relationships
    policy: Mapped[TransferPolicy] = relationship(back_populates="transfers")
    dest: Mapped[DestinationPolicy] = relationship(foreign_keys=[dest_id])
    states: Mapped[list[State]] = relationship(order_by="State.id.desc()", cascade="all, delete-orphan", foreign_keys="State.request_id")
    current_state: Mapped[State | None] = relationship(foreign_keys=[current_state_id], viewonly=True, post_update=True)

    @property
    def avg_data_rate(self) -> float:
        d_rate = 0 if self.download_rate is None else self.download_rate
        u_rate = 0 if self.upload_rate is None else self.upload_rate
        return round((d_rate + u_rate) / 2, 2)
