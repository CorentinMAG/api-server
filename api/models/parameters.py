from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class TransferParameters(SQLBase):
    __tablename__ = "transfer_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    max_retry: Mapped[int] = mapped_column(default=5)
    retry_delay: Mapped[int] = mapped_column(default=30)
    retentions: Mapped[int] = mapped_column(default=30)
    pattern: Mapped[str]
    compress: Mapped[bool] = mapped_column(default=False)
    compress_type: Mapped[str | None]
    data_type: Mapped[str]

    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id"))

    periodical: Mapped["PeriodicalParameters"] = relationship()

class PeriodicalParameters(SQLBase):
    __tablename__ = "periodical_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    polling_interval: Mapped[int]

    parameters_id: Mapped[int] = mapped_column(ForeignKey("transfer_parameters.id"))


class GlobalParameters(SQLBase):
    __tablename__ = "global_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(default="online")

class KafkaParameters(SQLBase):
    __tablename__ = "kafka_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    replica: Mapped[int] = mapped_column(default=1)
    partitions: Mapped[int] = mapped_column(default=1)
    server_id: Mapped[int] = mapped_column(ForeignKey("notification_servers.id"))
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id"))

