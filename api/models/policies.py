from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase
from dtr_common.constantes import Type

if TYPE_CHECKING:
    from .parameters import TransferPolicyParameters, ServerParameters
    from .queue import Queue
    from .request import TransferRequest
    from .target import Target


class SourcePolicy(SQLBase, SerializerMixin):
    __tablename__ = "source_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    purge: Mapped[bool] = mapped_column(default=False)
    path: Mapped[str | None]
    bucket: Mapped[str | None]
    pattern: Mapped[str]

    src_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    target: Mapped[Target] = relationship()


class DestinationPolicy(SQLBase, SerializerMixin):
    __tablename__ = "destination_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str | None]
    bucket: Mapped[str | None]

    dest_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))
    request_id: Mapped[int | None] = mapped_column(ForeignKey("transfer_requests.id"))
    target: Mapped[Target] = relationship()
    tmp_prefix: Mapped[str | None]
    final_prefix: Mapped[str | None]


class TransferPolicy(SQLBase, SerializerMixin):
    __tablename__ = "transfer_policies"

    serialize_only = (
        "id",
        "name",
        "enabled",
        "type",
        "notifications",
        "src",
        "dests",
        "parameters",
        "queue",
        "created_at",
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    type: Mapped[Type]

    notifications: Mapped[list[ServerParameters]] = relationship()

    src: Mapped[SourcePolicy] = relationship()
    src_id: Mapped[int] = mapped_column(ForeignKey("source_policies.id", ondelete="CASCADE"))

    dests: Mapped[list[DestinationPolicy]] = relationship()

    parameters: Mapped[TransferPolicyParameters] = relationship()
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"))
    queue: Mapped[Queue] = relationship()
    transfers: Mapped[list[TransferRequest]] = relationship(back_populates="policy")
    created_at: Mapped[str] = mapped_column(DateTime, default=func.now())

    @property
    def has_notifications(self) -> bool:
        return bool(self.notifications)

    def update(self, mapping: dict):
        update_rec(self, mapping)


def update_rec(obj: SQLBase, mapping: dict):
    """
    recursive update
    """
    for key, value in mapping.items():
        if key in obj.__mapper__.relationships:
            relation = getattr(obj, key)
            update_rec(relation, value)
        elif key in obj.__mapper__.column_attrs:
            setattr(obj, key, value)
