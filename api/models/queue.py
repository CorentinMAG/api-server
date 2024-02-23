from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey
import uuid
from sqlalchemy_serializer import SerializerMixin

class Queue(SQLBase, SerializerMixin):
    __tablename__ = "queues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    max_requests: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer)