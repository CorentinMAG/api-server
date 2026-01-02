from api.models import Queue
from .base import BaseRepository
from api.exceptions import NotFoundException
from sqlalchemy import select


class QueueRepository(BaseRepository[Queue]):

    def get_by_name(self, name: str) -> Queue:
        query = select(Queue).where(Queue.name == name)

        queue = self.session.scalar(query)
        if not queue:
            raise NotFoundException(f"queue with name {name} not found")
        return queue

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[Queue]:
        query = select(Queue)
        if filters:
            self.filters(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).unique().all())
