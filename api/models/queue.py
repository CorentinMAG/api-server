from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import BaseModel


class Queue(BaseModel, SerializerMixin):
    __tablename__ = "queues"

    serialize_only = (
        "name",
        "uid",
        "priority",
        "timeout",
        "limit",
        "threshold",
    )

    name: Mapped[str] = mapped_column(unique=True, index=True)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    priority: Mapped[int] = mapped_column(index=True)
    timeout: Mapped[int | None] = mapped_column(default=86400)
    limit: Mapped[int | None] = mapped_column(default=100)
    threshold: Mapped[int | None] = mapped_column(default=80)
