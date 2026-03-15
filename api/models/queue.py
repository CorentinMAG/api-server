from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from typing import TYPE_CHECKING
from .base import Base
from .association import association_table
from .mixin import ParametersConfigMixin

if TYPE_CHECKING:
    from .worker import Worker


class Queue(Base, SerializerMixin, ParametersConfigMixin):
    __tablename__ = "queues"

    serialize_only = (
        "name",
        "uid",
        "priority",
        "queue_timeout",
        "queue_limit",
        "queue_threshold",
    )

    name: Mapped[str] = mapped_column(unique=True, index=True)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    priority: Mapped[int] = mapped_column(index=True)
    queue_timeout: Mapped[int] = mapped_column()
    queue_limit: Mapped[int] = mapped_column()
    queue_threshold: Mapped[int] = mapped_column()

    workers: Mapped[list[Worker]] = relationship(
        secondary=association_table, back_populates="queues", passive_deletes=True
    )
