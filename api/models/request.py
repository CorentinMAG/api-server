from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase
from .states import State

if TYPE_CHECKING:
    from .policies import TransferPolicy, DestinationPolicy


class TransferRequest(SQLBase, SerializerMixin):
    __tablename__ = "transfer_requests"

    serialize_only = (
        "id",
        "filename",
        "size",
        "uid",
        "states",
        "policy",
        "created_at",
        "nb_retry",
        "next_retry_min_time",
        "start",
        "end",
        "download_rate",
        "download_time",
        "upload_rate",
        "upload_time",
        "dest",
        "src_relative_path",
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    size: Mapped[float | None] = mapped_column(default=None)  # in MB
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    states: Mapped[list[State]] = relationship(order_by="State.id.desc()")
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("transfer_policies.id", ondelete="SET NULL"))
    policy: Mapped[TransferPolicy] = relationship(back_populates="transfers")
    created_at: Mapped[str] = mapped_column(DateTime, default=func.now(), index=True)
    nb_retry: Mapped[int] = mapped_column(default=0)
    next_retry_min_time: Mapped[str | None] = mapped_column(DateTime, default=None)
    start: Mapped[str | None] = mapped_column(DateTime, default=None)
    end: Mapped[str | None] = mapped_column(DateTime, default=None)
    download_rate: Mapped[float | None]
    download_time: Mapped[float | None]
    upload_rate: Mapped[float | None]
    upload_time: Mapped[float | None]
    dest_id: Mapped[int | None] = mapped_column(ForeignKey("destination_policies.id", ondelete="SET NULL"))
    dest: Mapped[DestinationPolicy] = relationship(foreign_keys=[dest_id])
    src_relative_path: Mapped[str | None]

    def update(self, mapping: dict):
        for key, value in mapping.items():
            if key in self.__mapper__.column_attrs.keys():
                setattr(self, key, value)

    def clone(self) -> TransferRequest:
        return self.__class__(
            **{
                c.name: getattr(self, c.name)
                for c in self.__table__.columns
                if c.name
                not in (
                    "id",
                    "uid",
                    "created_at",
                    "download_rate",
                    "download_time",
                    "upload_rate",
                    "upload_time",
                )
            }
        )
