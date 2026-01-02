from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
from .policies import TransferPolicy
from sqlalchemy_serializer import SerializerMixin


class Trigger(BaseModel, SerializerMixin):
    __tablename__ = "triggers"

    serialize_only = ("name", "polling_interval")

    name: Mapped[str] = mapped_column(unique=True, index=True)
    polling: Mapped[int]
    policies: Mapped[list[TransferPolicy]] = relationship()
