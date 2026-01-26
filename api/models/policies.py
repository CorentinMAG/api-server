from __future__ import annotations

from typing import TYPE_CHECKING

from api.dtr_common.constantes import Type
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import BaseModel

if TYPE_CHECKING:
    from .parameters import TransferPolicyParameters
    from .queue import Queue
    from .request import TransferRequest
    from .target import Target
    from .trigger import Trigger
    from .notifications import Notification


class SourcePolicy(BaseModel, SerializerMixin):
    __tablename__ = "source_policies"

    serialize_only = (
        "purge",
        "path",
        "bucket",
        "pattern",
        "target",
    )

    purge: Mapped[bool] = mapped_column(default=False)
    path: Mapped[str | None]
    bucket: Mapped[str | None]
    pattern: Mapped[str]

    src_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))

    target: Mapped[Target] = relationship(lazy="joined")


class DestinationPolicy(BaseModel, SerializerMixin):
    __tablename__ = "destination_policies"

    serialize_only = (
        "path",
        "bucket",
        "target",
        "tmp_prefix",
        "final_prefix",
        "notifications",
        "path_from_filename_delimiter",
        "path_from_filename_expression",
    )

    path: Mapped[str | None]
    bucket: Mapped[str | None]
    tmp_prefix: Mapped[str | None]
    final_prefix: Mapped[str | None]
    path_from_filename_delimiter: Mapped[str | None]
    path_from_filename_expression: Mapped[list[str] | None] = mapped_column(JSON)

    dest_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("transfer_policies.id", ondelete="RESTRICT")
    )

    target: Mapped[Target] = relationship(lazy="joined")
    notifications: Mapped[list[Notification]] = relationship(passive_deletes=True)


class TransferPolicy(BaseModel, SerializerMixin):
    __tablename__ = "transfer_policies"

    serialize_only = (
        "id",
        "created_at",
        "name",
        "enabled",
        "type",
        "src",
        "dests",
        "parameters",
        "queue",
    )

    name: Mapped[str] = mapped_column(unique=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    type: Mapped[Type]

    src_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_policies.id", ondelete="RESTRICT"), unique=True
    )
    queue_id: Mapped[int | None] = mapped_column(
        ForeignKey("queues.id", ondelete="RESTRICT")
    )
    trigger_id: Mapped[int | None] = mapped_column(
        ForeignKey("triggers.id", ondelete="RESTRICT")
    )

    src: Mapped[SourcePolicy] = relationship(
        lazy="joined",
        passive_deletes=True,
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )
    dests: Mapped[list[DestinationPolicy]] = relationship(
        passive_deletes=True, cascade="all, delete-orphan"
    )
    parameters: Mapped[TransferPolicyParameters] = relationship(
        lazy="joined",
        passive_deletes=True,
        single_parent=True,
        uselist=False,
        cascade="all, delete-orphan",
    )
    trigger: Mapped[Trigger] = relationship()
    queue: Mapped[Queue] = relationship(lazy="joined")
    transfers: Mapped[list[TransferRequest]] = relationship(back_populates="policy")
