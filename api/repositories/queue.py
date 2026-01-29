from sqlalchemy.orm import selectinload
from sqlalchemy import select
from .base import BaseRepository
from api.models import Queue
from api.exception import NotFoundException

class QueueRepository(BaseRepository[Queue]):
    """repository for queue operations"""

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
            raise NotFoundException(f"Target with name {name} not found")
        return obj
    
    def get_with_relations(self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None) -> list[Queue]:
        query = (
            select(Queue)
            .options(
                selectinload(Queue.workers)
            )
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = self._filter(query, filters)
        return list(self.session.scalars(query).unique().all())