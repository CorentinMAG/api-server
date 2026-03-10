from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import BaseModel
from .queue import Queue

association_table = Table(
    "worker_queues",
    BaseModel.metadata,
    Column("worker_id", ForeignKey("workers.id"), primary_key=True),
    Column("queue_id", ForeignKey("queues.id"), primary_key=True),
)


class Worker(BaseModel, SerializerMixin):
    """Model representing a worker instance."""

    __tablename__ = "workers"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    queues: Mapped[list[Queue]] = relationship(secondary=association_table)
