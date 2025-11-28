from .base import Base
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from .queue import Queue

# To create a Many to Many relationship
association_table = Table(
    "worker_queues",
    Base.metadata,
    Column("worker_id", ForeignKey("workers.id")),
    Column("queue_id", ForeignKey("queues.id"))
)

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