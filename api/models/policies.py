from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase
from dtr_common.constantes import Type

if TYPE_CHECKING:
    from .parameters import KafkaTopicParameters, TransferPolicyParameters
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
    target: Mapped[Target] = relationship()
    tmp_prefix_dest: Mapped[str | None]
    final_prefix_dest: Mapped[str | None]


class TransferPolicy(SQLBase, SerializerMixin):
    __tablename__ = "transfer_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    type: Mapped[Type]  # deprecated

    kafka: Mapped[list[KafkaTopicParameters]] = relationship()

    src: Mapped[SourcePolicy] = relationship()
    src_id: Mapped[int] = mapped_column(ForeignKey("source_policies.id", ondelete="CASCADE"))

    dest: Mapped[DestinationPolicy] = relationship()
    dest_id: Mapped[int] = mapped_column(ForeignKey("destination_policies.id", ondelete="CASCADE"))

    parameters: Mapped[TransferPolicyParameters] = relationship()
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"))
    queue: Mapped[Queue] = relationship()
    transfers: Mapped[list[TransferRequest]] = relationship(back_populates="policy")
    created_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)
  

    @property
    def has_notifications(self) -> bool:
        return bool(self.kafka)
    
