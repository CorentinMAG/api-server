from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .policies import TransferPolicy
from sqlalchemy_serializer import SerializerMixin


class Trigger(Base, SerializerMixin):
    __tablename__ = "triggers"

    serialize_only = (
        "id",
        "created_at",
        "updated_at",
        "name",
        "polling_interval"
    )

    name: Mapped[str] = mapped_column(unique=True, index = True)
    polling_interval: Mapped[int] = mapped_column(comment="in seconds")

    # relations
    policies: Mapped[list[TransferPolicy]] = relationship(back_populates="trigger")