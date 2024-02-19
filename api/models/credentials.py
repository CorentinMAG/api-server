from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from sqlalchemy_serializer import SerializerMixin

class Credentials(SQLBase, SerializerMixin):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(50))
    token: Mapped[str] = mapped_column(String(200), nullable=True)
    type: Mapped[str] = mapped_column(String(10), default="password")
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"), nullable=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"), nullable=True)