from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from api.exceptions import NotFoundException
from api.models import NotificationServer

from .base import BaseRepository


class NotificationServerRepository(BaseRepository[NotificationServer]):
    """repository for notification servers"""

    def get_by_name(self, name: str) -> NotificationServer:
        """get notification server by name"""

        query = (
            select(NotificationServer)
            .where(NotificationServer.name == name)
            .options(joinedload(NotificationServer.credentials))
        )

        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"NotificationServer with name {name} not found")
        return obj

    def get_by_type(self, server_type: str, skip: int = 0, limit: int = 0) -> list[NotificationServer]:
        query = (
            select(NotificationServer).where(NotificationServer.type == server_type).offset(skip).limit(limit)
        )
        return list(self.session.scalars(query).all())

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[NotificationServer]:
        query = select(NotificationServer).options(joinedload(NotificationServer.credentials))
        if filters:
            self.filters(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).unique().all())
