from flask_sqlalchemy import SQLAlchemy
from .base import BaseRepository
from ..models import TransferPolicy, DestinationPolicy
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from ..errors import NotFoundError
from dtr_common.constantes import Type


class TransferPolicyRepository(BaseRepository[TransferPolicy]):
    """Repository for TransferPolicy operations"""

    def __init__(self, db: SQLAlchemy):
        super().__init__(TransferPolicy, db)

    def get_by_name(self, name: str) -> TransferPolicy:
        query = (
            select(TransferPolicy)
            .where(TransferPolicy.name == name)
            .options(
                selectinload(TransferPolicy.dests).joinedload(DestinationPolicy.target),
                selectinload(TransferPolicy.dests).selectinload(DestinationPolicy.notifications),
                joinedload(TransferPolicy.parameters),
                joinedload(TransferPolicy.queue)
            )
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"TransferPolicy with name {name} not found")

    def get_enabled(self, type: Type | None = None, skip: int = 0, limit: int = 100) -> list[TransferPolicy]:
        query = (
            select(TransferPolicy)
            .where(TransferPolicy.enabled == True)
        )
        if type:
            query = query.where(TransferPolicy.type == type)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())