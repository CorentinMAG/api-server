from .base import BaseRepository
from api.models import Worker
from api.exception import NotFoundException
from sqlalchemy import select


class WorkerRepository(BaseRepository[Worker]):

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[Worker]:
        query = select(Worker)
        if filters:
            query = self._filter(filters, query)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).unique().all())
