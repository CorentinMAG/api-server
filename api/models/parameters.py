from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from dtr_common.constantes import Mode
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase

if TYPE_CHECKING:
    from .server import NotificationServer


class PeriodicalParameters(SQLBase, SerializerMixin):
    __tablename__ = "periodical_parameters"

    serialize_only = ("polling_interval", "next_polling_min_time")

    id: Mapped[int] = mapped_column(primary_key=True)
    polling_interval: Mapped[int]
    parameter_id: Mapped[int] = mapped_column(ForeignKey("transfer_policy_parameters.id", ondelete="CASCADE"))
    next_polling_min_time: Mapped[str | None] = mapped_column(DateTime, default=None)


class TransferPolicyParameters(SQLBase, SerializerMixin):
    __tablename__ = "transfer_policy_parameters"

    serialize_only = (
        "max_retry",
        "retry_delay",
        "transfer_requests_history",
        "compress",
        "compress_type",
        "only_new_data",
        "transfer_timeout",
        "periodical",
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    max_retry: Mapped[int | None]
    retry_delay: Mapped[int | None]  # in seconds
    transfer_requests_history: Mapped[int | None]
    compress: Mapped[bool | None]
    compress_type: Mapped[str | None]
    only_new_data: Mapped[bool | None]
    transfer_timeout: Mapped[int | None]  # in seconds

    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))
    periodical: Mapped[PeriodicalParameters] = relationship()


class GlobalParameters(SQLBase, SerializerMixin):
    __tablename__ = "global_parameters"

    serialize_only = (
        "mode",
        "tmp_prefix",
        "final_prefix",
        "retry_delay",
        "max_retry",
        "transfer_requests_history",
        "compress",
        "only_new_data",
        "transfer_timeout",
        "queue_timeout",
        "polling_interval",
        "queue_limit",
        "queue_threshold",
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[Mode] = mapped_column(default=Mode.ONLINE)
    updated_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tmp_prefix: Mapped[str | None]
    final_prefix: Mapped[str | None]
    retry_delay: Mapped[int] = mapped_column(default=3600)  # in seconds
    max_retry: Mapped[int] = mapped_column(default=5)
    transfer_requests_history: Mapped[int] = mapped_column(default=31)
    compress: Mapped[bool] = mapped_column(default=False)
    only_new_data: Mapped[bool] = mapped_column(default=True)
    transfer_timeout: Mapped[int] = mapped_column(default=300)  # in seconds
    queue_timeout: Mapped[int] = mapped_column(default=86400)  # in seconds
    polling_interval: Mapped[int] = mapped_column(default=10)  # in seconds
    queue_limit: Mapped[int] = mapped_column(default=100)
    queue_threshold: Mapped[int] = mapped_column(default=80)


class TargetParameters(SQLBase, SerializerMixin):
    __tablename__ = "target_parameters"

    serialize_only = ("use_ssl", "verify")

    id: Mapped[int] = mapped_column(primary_key=True)
    use_ssl: Mapped[bool] = mapped_column(default=True)
    verify: Mapped[bool] = mapped_column(default=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id"))


class ServerParameters(SQLBase):
    __tablename__ = "server_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]  # discriminator column to differentiate parameter types
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))

    __mapper_args__ = {"polymorphic_identity": "transfer_parameters", "polymorphic_on": "type"}


class KafkaTopicParameters(ServerParameters, SerializerMixin):
    __tablename__ = "kafka_topic_parameters"

    serialize_only = ("topic", "replica", "partitions", "server")

    id: Mapped[int] = mapped_column(ForeignKey("server_parameters.id"), primary_key=True)
    topic: Mapped[str]
    replica: Mapped[int] = mapped_column(default=1)
    partitions: Mapped[int] = mapped_column(default=1)
    server_id: Mapped[int] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"))
    server: Mapped[NotificationServer] = relationship()

    __mapper_args__ = {"polymorphic_identity": "kafka_topic_parameters"}
