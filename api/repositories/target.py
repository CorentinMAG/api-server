from sqlalchemy.orm import joinedload
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from .base import BaseRepository
from ..models import Target
from ..errors import NotFoundError

class TargetRepository(BaseRepository[Target]):
    """repository for target operations"""

    def __init__(self, db: SQLAlchemy):
        super().__init__(Target, db)

    def get_by_name(self, name: str) -> Target:
        query = (
            select(Target)
            .where(Target.name == name)
            .options(
                joinedload(Target.credentials), 
                joinedload(Target.parameters)
            )
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"Target with name {name} not found")
        return obj
    
    def get_all_with_relations(self, skip: int = 0, limit: int = 0) -> list[Target]:
        query = (
            select(Target)
            .options(
                joinedload(Target.credentials),
                joinedload(Target.parameters)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(query).unique().all())