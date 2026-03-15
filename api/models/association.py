from sqlalchemy import Table, ForeignKey, Column
from .base import Base

# To create a Many to Many relationship
association_table = Table(
    "worker_queues",
    Base.metadata,
    Column("worker_id", ForeignKey("workers.id", ondelete="CASCADE"), primary_key=True),
    Column("queue_id", ForeignKey("queues.id", ondelete="CASCADE"), primary_key=True),
)
