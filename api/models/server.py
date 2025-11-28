from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base

if TYPE_CHECKING:
    from .credentials import Credentials


class NotificationServer(Base, SerializerMixin):
    __tablename__ = "notification_servers"

    serialize_only = ("name", "type", "host", "port", "credentials", "timeout")

    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[str]
    host: Mapped[str]
    port: Mapped[int]
    credentials: Mapped[Credentials] = relationship(lazy="joined")
    timeout: Mapped[int] = mapped_column(default=40)
