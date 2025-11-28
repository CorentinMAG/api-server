from __future__ import annotations

from typing import TYPE_CHECKING

from dtr_common.constantes import Protocol
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base

if TYPE_CHECKING:
    from .credentials import Credentials
    from .parameters import TargetParameters


class Target(Base, SerializerMixin):
    __tablename__ = "targets"

    serialize_only = ("name", "protocol", "port", "host", "credentials", "parameters")

    name: Mapped[str] = mapped_column(unique=True)
    protocol: Mapped[Protocol]
    port: Mapped[int]
    host: Mapped[str]
    credentials: Mapped[Credentials] = relationship(lazy="joined")
    parameters: Mapped[TargetParameters] = relationship(lazy="joined")
