from .base import BaseRepository
from api.models import Trigger, TransferPolicy
from api.exception import NotFoundException
from sqlalchemy import select, func, Select
from sqlalchemy.orm import selectinload
from typing import NamedTuple


class ITriggerPaginate(NamedTuple):
    page: int
    per_page: int
    pages: int
    total: int
    items: list[TransferPolicy]


class TriggerRepository(BaseRepository[Trigger]):

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[Trigger]:
        query = select(Trigger)
        if filters:
            query = self._filter(filters, query)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).unique().all())
