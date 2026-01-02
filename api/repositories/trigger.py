from .base import BaseRepository
from api.models import Trigger
from sqlalchemy import select
from api.exceptions import NotFoundException


class TriggerRepository(BaseRepository[Trigger]):

    def get_by_name(self, name: str) -> Trigger:
        """get trigger by name"""

        query = select(Trigger).where(Trigger.name == name)

        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"Trigger with name {name} not found")
        return obj

    def get_with_relations(
        self, skip: int, limit: int, filters: dict[str, any] | None = None
    ):
        query = select(Trigger)
        if filters:
            self.filters(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())
