from sqlalchemy.orm import joinedload
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from .base import BaseRepository
from ..models import NotificationServer
from ..errors import NotFoundError

class NotificationServerRepository(BaseRepository[NotificationServer]):
    """repository for target operations"""

    def __init__(self, db: SQLAlchemy):
        super().__init__(NotificationServer, db)

    def get_by_name(self, name: str) -> NotificationServer:
        query = (
            select(NotificationServer)
            .where(NotificationServer.name == name)
            .options(
                joinedload(NotificationServer.credentials), 
            )
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"NotificationServer with name {name} not found")
        return obj
    
    def get_all_with_relations(self, skip: int = 0, limit: int = 0) -> list[NotificationServer]:
        query = (
            select(NotificationServer)
            .options(
                joinedload(NotificationServer.credentials),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(query).unique().all())