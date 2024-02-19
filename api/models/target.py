from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from sqlalchemy_serializer import SerializerMixin

class Target(SQLBase, SerializerMixin):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    protocol: Mapped[str] = mapped_column(String(10))
    port: Mapped[int] = mapped_column(Integer)
    host: Mapped[str] = mapped_column(String(50))
    bucket: Mapped[str] = mapped_column(String(30), nullable=True)
    credentials: Mapped["Credentials"] = relationship()
