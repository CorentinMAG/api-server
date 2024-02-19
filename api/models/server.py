from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from sqlalchemy_serializer import SerializerMixin

class NotificationServer(SQLBase, SerializerMixin):
    __tablename__ = "notification_servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique = True)
    type: Mapped[str] = mapped_column(String(10))
    host: Mapped[str] = mapped_column(String(30))
    port: Mapped[int]
    credentials: Mapped["Credentials"] = relationship()
    timeout: Mapped[int] = mapped_column(default=40)
    parameters: Mapped[list["KafkaParameters"]] = relationship()


