from sqlalchemy.orm import selectinload
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from .base import BaseRepository
from ..models import Queue
from ..errors import NotFoundError

class QueueRepository(BaseRepository[Queue]):
    """repository for target operations"""

    def __init__(self, db: SQLAlchemy):
        super().__init__(Queue, db)

    def get_by_name(self, name: str) -> Queue:
        query = (
            select(Queue)
            .where(Queue.name == name)
            .options(
              selectinload(Queue.workers)
            )
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"Target with name {name} not found")
        return obj
    
    def get_all_with_relations(self, skip: int = 0, limit: int = 100) -> list[Queue]:
        query = (
            select(Queue)
            .options(
                selectinload(Queue.workers)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(query).unique().all())
    
    def get_by_priority(self, skip: int = 0, limit: int = 100) -> list[Queue]:
        """get queues ordered by priority"""
        query = (
            select(Queue)
            .order_by(Queue.priority.asc())
            .options(
                selectinload(Queue.workers)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(query).all())