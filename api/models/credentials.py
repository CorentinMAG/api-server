from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase


class Credentials(SQLBase, SerializerMixin):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str]
    password: Mapped[str]
    token: Mapped[str | None]
    type: Mapped[str] = mapped_column(default="password")
    target_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    server_id: Mapped[int | None] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"))
