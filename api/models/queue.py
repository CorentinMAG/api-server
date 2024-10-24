from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase


class Queue(SQLBase, SerializerMixin):
    __tablename__ = "queues"

    serialize_only = ("name", "uid", "priority", "queue_timeout", "queue_limit", "queue_threshold")

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    priority: Mapped[int]
    queue_timeout: Mapped[int | None] = mapped_column(default=300)
    queue_limit: Mapped[int | None] = mapped_column(default=100)
<<<<<<< HEAD
    queue_threshold: Mapped[int| None] = mapped_column(default=80)
=======
    queue_threshold: Mapped[int | None] = mapped_column(default=80)
>>>>>>> main
