from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Queue(Base, SerializerMixin):
    __tablename__ = "queues"

    serialize_only = ("name", "uid", "priority", "queue_timeout", "queue_limit", "queue_threshold")

    name: Mapped[str] = mapped_column(unique=True)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    priority: Mapped[int] = mapped_column(index=True)
    queue_timeout: Mapped[int | None] = mapped_column(default=86400)
    queue_limit: Mapped[int | None] = mapped_column(default=100)
    queue_threshold: Mapped[int | None] = mapped_column(default=80)
