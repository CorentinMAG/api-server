from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from api.exceptions import NotFoundException
from api.models import Target

from .base import BaseRepository


class TargetRepository(BaseRepository[Target]):
    """repository for Target model"""

    def get_by_name(self, name: str) -> Target:
        """Get Target by name"""

        query = (
            select(Target)
            .where(Target.name == name)
            .options(joinedload(Target.credentials), joinedload(Target.parameters))
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"Target with name {name} not found")
        return obj

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[Target]:
        query = select(Target).options(joinedload(Target.credentials), joinedload(Target.parameters))
        if filters:
            self.filters(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).unique().all())
