from __future__ import annotations

from typing import TYPE_CHECKING

from dtr_common.constantes import Type
from sqlalchemy import JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase

if TYPE_CHECKING:
    from .parameters import ServerParameters, TransferPolicyParameters
    from .queue import Queue
    from .request import TransferRequest
    from .target import Target


class SourcePolicy(SQLBase, SerializerMixin):
    __tablename__ = "source_policies"

    # Include nested target to expose protocol/host/... in API serialization,
    # but avoid potentially sensitive credential secrets.
    # Credentials.password is already a SecretStr which serializes to "********";
    # if additional masking is needed, adapt serialize_rules.
    serialize_only = (
        "id",
        "purge",
        "path",
        "bucket",
        "pattern",
        "target",  # nested Target will include protocol
    )

    # Prevent lazy loading of heavy relationships or circular refs (eg. backrefs)
    serialize_rules = (
        # Do not expose secrets like target.parameters.secret_key, but keep password available
        # for internal services (trigger/worker) that still rely on it.
        "-target.parameters.secret_key",
    )

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
    # request_id: Mapped[int | None] = mapped_column(ForeignKey("transfer_requests.id"))
    target: Mapped[Target] = relationship()
    tmp_prefix: Mapped[str | None]
    final_prefix: Mapped[str | None]
    path_from_filename_delimiter: Mapped[str | None]
    path_from_filename_expression: Mapped[list[str] | None] = mapped_column(JSON)
    notifications: Mapped[list[ServerParameters]] = relationship()


class TransferPolicy(SQLBase, SerializerMixin):
    __tablename__ = "transfer_policies"

    serialize_only = (
        "id",
        "name",
        "enabled",
        "type",
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

    src: Mapped[SourcePolicy] = relationship()
    src_id: Mapped[int] = mapped_column(ForeignKey("source_policies.id", ondelete="CASCADE"))

    dests: Mapped[list[DestinationPolicy]] = relationship()

    parameters: Mapped[TransferPolicyParameters] = relationship()
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"))
    queue: Mapped[Queue] = relationship()
    transfers: Mapped[list[TransferRequest]] = relationship(back_populates="policy")
    created_at: Mapped[str] = mapped_column(DateTime, default=func.now())

    def update(self, mapping: dict):
        update_rec(self, mapping)


def update_rec(obj: SQLBase, mapping: dict):
    """
    recursive update
    """
    for key, value in mapping.items():
        if key in obj.__mapper__.relationships:
            relation = getattr(obj, key)
            if relation is not None:
                update_rec(relation, value)
        elif key in obj.__mapper__.column_attrs:
            setattr(obj, key, value)
