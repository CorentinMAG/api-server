from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from .queue import Queue
from .association import association_table


class Worker(Base, SerializerMixin):
    __tablename__ = "workers"

    serialize_only = (
        "id",
        "created_at",
        "updated_at",
        "name"
    )

    name: Mapped[str] = mapped_column(unique=True, index = True)
    queues: Mapped[list[Queue]] = relationship(secondary=association_table)