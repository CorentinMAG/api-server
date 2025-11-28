from __future__ import annotations

from typing import TYPE_CHECKING

from dtr_common.constantes import Type
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base

if TYPE_CHECKING:
    from .parameters import ServerParameters, TransferPolicyParameters
    from .queue import Queue
    from .request import TransferRequest
    from .target import Target
    from .trigger import Trigger


class SourcePolicy(Base, SerializerMixin):
    __tablename__ = "source_policies"

    # Include nested target to expose protocol/host/... in API serialization,
    # but avoid potentially sensitive credential secrets.
    # Credentials.password is already a SecretStr which serializes to "********";
    # if additional masking is needed, adapt serialize_rules.
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

    src_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    target: Mapped[Target] = relationship(lazy="joined")


class DestinationPolicy(Base, SerializerMixin):
    __tablename__ = "destination_policies"

    serialize_only = (
        "path",
        "bucket",
        "target",
        "tmp_prefix",
        "final_prefix",
        "path_from_filename_delimiter",
        "path_from_filename_expression"
    )

    path: Mapped[str | None]
    bucket: Mapped[str | None]

    dest_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))

    target: Mapped[Target | None] = relationship(lazy="joined")
    tmp_prefix: Mapped[str | None]
    final_prefix: Mapped[str | None]
    path_from_filename_delimiter: Mapped[str | None]
    path_from_filename_expression: Mapped[list[str] | None] = mapped_column(JSON)
    notifications: Mapped[list[ServerParameters]] = relationship()


class TransferPolicy(Base, SerializerMixin):
    __tablename__ = "transfer_policies"


    name: Mapped[str] = mapped_column(unique=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    type: Mapped[Type]

    # foreign keys
    src_id: Mapped[int | None] = mapped_column(ForeignKey("source_policies.id", ondelete="CASCADE"))
    queue_id: Mapped[int | None] = mapped_column(ForeignKey("queues.id", ondelete="CASCADE"))
    trigger_id: Mapped[int | None] = mapped_column(ForeignKey("triggers.id"))

    # relations
    src: Mapped[SourcePolicy] = relationship(lazy="joined")
    dests: Mapped[list[DestinationPolicy]] = relationship()
    parameters: Mapped[TransferPolicyParameters] = relationship()
    queue: Mapped[Queue] = relationship()
    transfers: Mapped[list[TransferRequest]] = relationship(back_populates="policy")
    trigger: Mapped[Trigger] = relationship(foreign_keys=[trigger_id], post_update=True)
