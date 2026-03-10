from __future__ import annotations

from sqlalchemy import select

from api.exceptions import NotFoundException
from api.models import Worker

from .base import BaseRepository


class WorkerRepository(BaseRepository[Worker]):
    def get_by_name(self, name: str) -> Worker:
        """get Worker by name"""

        query = select(Worker).where(Worker.name == name)
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"Worker with name {name} not found")
        return obj

    def get_with_relations(self, skip: int, limit: int, filters: dict[str, any] | None = None):
        query = select(Worker)
        if filters:
            self.filters(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())
