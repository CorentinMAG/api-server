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

    id: Mapped[int] = mapped_column(primary_key=True)
    polling_interval: Mapped[int]
    parameter_id: Mapped[int] = mapped_column(ForeignKey("transfer_policy_parameters.id", ondelete="CASCADE"))
    next_polling_min_time: Mapped[str | None] = mapped_column(DateTime, default=None)


class TransferPolicyParameters(SQLBase, SerializerMixin):
    __tablename__ = "transfer_policy_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    max_retry: Mapped[int | None]
    retry_delay: Mapped[int | None]  # in seconds
    transfer_requests_history: Mapped[int | None]
    compress: Mapped[bool | None]
    compress_type: Mapped[str | None]
    data_type: Mapped[str]
    only_new_data: Mapped[bool | None]
    transfer_timeout: Mapped[int | None]  # in seconds

    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))
    periodical: Mapped[PeriodicalParameters] = relationship()


class GlobalParameters(SQLBase, SerializerMixin):
    __tablename__ = "global_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[Mode] = mapped_column(default=Mode.ONLINE)
    updated_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tmp_prefix_dest: Mapped[str | None]
    final_prefix_dest: Mapped[str | None]
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


class KafkaTopicParameters(SQLBase, SerializerMixin):
    __tablename__ = "kafka_topic_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    replica: Mapped[int] = mapped_column(default=1)
    partitions: Mapped[int] = mapped_column(default=1)
    server_id: Mapped[int] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"))
    server: Mapped[NotificationServer] = relationship()
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))
