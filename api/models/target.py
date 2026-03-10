from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from api.dtr_common.constantes import Protocol

from .base import BaseModel

if TYPE_CHECKING:
    from .credentials import Credentials
    from .parameters import TargetParameters


class Target(BaseModel, SerializerMixin):
    __tablename__ = "targets"

    serialize_only = ("name", "protocol", "port", "host", "credentials", "parameters")

    name: Mapped[str] = mapped_column(unique=True, index=True)
    protocol: Mapped[Protocol]
    port: Mapped[int]
    host: Mapped[str]
    credentials: Mapped[Credentials] = relationship(lazy="joined", passive_deletes=True)
    parameters: Mapped[TargetParameters] = relationship(lazy="joined", passive_deletes=True)
