from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from common.constantes import Mode
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

    parameters_id: Mapped[int] = mapped_column(ForeignKey("transfer_parameters.id"))


class TransferParameters(SQLBase, SerializerMixin):
    __tablename__ = "transfer_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    max_retry: Mapped[int] = mapped_column(default=5)
    retry_delay: Mapped[int] = mapped_column(default=30)
    retentions: Mapped[int] = mapped_column(default=30)
    pattern: Mapped[str]
    compress: Mapped[bool] = mapped_column(default=False)
    compress_type: Mapped[str | None]
    data_type: Mapped[str]

    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))

    periodical: Mapped[PeriodicalParameters] = relationship()


class GlobalParameters(SQLBase, SerializerMixin):
    __tablename__ = "global_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[Mode] = mapped_column(default=Mode.ONLINE)
    updated_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KafkaParameters(SQLBase, SerializerMixin):
    __tablename__ = "kafka_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    replica: Mapped[int] = mapped_column(default=1)
    partitions: Mapped[int] = mapped_column(default=1)
    server_id: Mapped[int] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"))
    server: Mapped[NotificationServer] = relationship()
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))
