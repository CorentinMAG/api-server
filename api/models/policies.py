from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin


class TransferPolicy(SQLBase, SerializerMixin):
    __tablename__ = "transfer_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique = True)
    enabled: Mapped[bool] = mapped_column(default = True)
    type: Mapped[str]

    kafka: Mapped[list["KafkaParameters"] | None] = relationship()

    src: Mapped["SourcePolicy"] = relationship()
    src_id: Mapped[int] = mapped_column(ForeignKey("source_policies.id", ondelete="CASCADE"))

    dest: Mapped["DestinationPolicy"] = relationship()
    dest_id: Mapped[int] = mapped_column(ForeignKey("destination_policies.id", ondelete="CASCADE"))

    parameters: Mapped["TransferParameters"] = relationship()
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"))
    queue: Mapped["Queue"] = relationship()
    transfers: Mapped[list["TransferRequest"]] = relationship(back_populates="policy")
    created_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def has_notifications(self) -> bool:
        return bool(self.kafka)


class SourcePolicy(SQLBase, SerializerMixin):
    __tablename__ = "source_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    purge: Mapped[bool] = mapped_column(default=False)
    path: Mapped[str | None]
    bucket: Mapped[str | None] = mapped_column(String(30))

    src_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    target: Mapped["Target"] = relationship()

class DestinationPolicy(SQLBase, SerializerMixin):
    __tablename__ = "destination_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str | None]
    bucket: Mapped[str | None] = mapped_column(String(30))

    dest_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    target: Mapped["Target"] = relationship()
