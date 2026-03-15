from sqlalchemy.orm import joinedload
from sqlalchemy import select
from .base import BaseRepository
from api.models import Target
from api.exception import NotFoundException


class TargetRepository(BaseRepository[Target]):
    """repository for target operations"""

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[Target]:
        query = select(Target).options(
            joinedload(Target.credentials), joinedload(Target.parameters)
        )
        if filters:
            query = self._filter(filters, query)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).unique().all())
