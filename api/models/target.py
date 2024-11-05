from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from dtr_common.constantes import Protocol

from ..db import Base as SQLBase

if TYPE_CHECKING:
    from .credentials import Credentials
    from .parameters import TargetParameters


class Target(SQLBase, SerializerMixin):
    __tablename__ = "targets"

    serialize_only = ("name", "protocol", "port", "host", "credentials", "parameters")

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    protocol: Mapped[Protocol]
    port: Mapped[int]
    host: Mapped[str]
    credentials: Mapped[Credentials] = relationship()
    parameters: Mapped[TargetParameters] = relationship()
