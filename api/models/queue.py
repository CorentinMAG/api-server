from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase


class Queue(SQLBase, SerializerMixin):
    __tablename__ = "queues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    priority: Mapped[int]
    queue_timeout: Mapped[int] = mapped_column(default=300)
    queue_limit: Mapped[int] = mapped_column(default=100)
