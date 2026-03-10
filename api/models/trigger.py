from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import BaseModel
from .policies import TransferPolicy


class Trigger(BaseModel, SerializerMixin):
    __tablename__ = "triggers"

    serialize_only = ("name", "polling_interval")

    name: Mapped[str] = mapped_column(unique=True, index=True)
    polling: Mapped[int]
    policies: Mapped[list[TransferPolicy]] = relationship()
