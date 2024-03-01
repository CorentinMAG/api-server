from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase

if TYPE_CHECKING:
    from .credentials import Credentials


class Target(SQLBase, SerializerMixin):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    protocol: Mapped[str] = mapped_column(String(10))
    port: Mapped[int] = mapped_column(Integer)
    host: Mapped[str] = mapped_column(String(50))
    credentials: Mapped[Credentials] = relationship()
