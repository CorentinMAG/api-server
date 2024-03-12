from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase

if TYPE_CHECKING:
    from .credentials import Credentials


class NotificationServer(SQLBase, SerializerMixin):
    __tablename__ = "notification_servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[str]
    host: Mapped[str]
    port: Mapped[int]
    credentials: Mapped[Credentials] = relationship()
    timeout: Mapped[int] = mapped_column(default=40)
