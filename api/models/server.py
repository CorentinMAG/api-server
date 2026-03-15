from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from dtr_common.constantes import ServerType

from .base import Base

if TYPE_CHECKING:
    from .credentials import Credentials
    from .notifications import Notification


class NotificationServer(Base, SerializerMixin):
    __tablename__ = "notification_servers"

    serialize_only = ("name", "type", "host", "port", "credentials", "timeout")

    name: Mapped[str] = mapped_column(unique=True, index=True)
    type: Mapped[ServerType]
    host: Mapped[str]
    port: Mapped[int]
    timeout: Mapped[int] = mapped_column(default=40)
    credentials: Mapped[Credentials] = relationship(lazy="joined", passive_deletes=True)
    notifications: Mapped[list[Notification]] = relationship(back_populates="server", passive_deletes=True)
