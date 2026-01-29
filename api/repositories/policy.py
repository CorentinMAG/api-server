from .base import BaseRepository
from api.models import TransferPolicy, DestinationPolicy
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from api.exception import NotFoundException
from typing import overload


class TransferPolicyRepository(BaseRepository[TransferPolicy]):
    """Repository for TransferPolicy operations"""

    def get_by_name(self, name: str) -> TransferPolicy:
        """get transfer policy by name"""
        query = (
            select(TransferPolicy)
            .where(TransferPolicy.name == name)
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"TransferPolicy with name {name} not found")
        return obj
    
    @overload
    def get_with_relations(self, id: int) -> TransferPolicy:
        ...
    
    @overload
    def get_with_relations(self, skip: int | None = None, limit: int | None = None, filters: dict[str, any] | None = None) -> list[TransferPolicy]:
        ...
    
    def get_with_relations(self, id: int, skip: int | None = None, limit: int | None = None, filters: dict[str, any] | None = None) -> TransferPolicy | list[TransferPolicy]:
        """get transfer policy/policies with all relations loaded """
        query = (
            select(TransferPolicy)
            .options(
                selectinload(TransferPolicy.dests).joinedload(DestinationPolicy.target),
                selectinload(TransferPolicy.dests).selectinload(DestinationPolicy.notifications),
                joinedload(TransferPolicy.parameters),
                joinedload(TransferPolicy.queue)
            )
        )

        if id is not None:
            query = query.where(TransferPolicy.id == id)
            obj = self.session.scalar(query)
            if not obj:
                raise NotFoundException(f"Transfer policy with id {id} not found")
            return obj
        else:
            if filters:
                query = self._filter(query, filters)
            query = query.offset(skip).limit(limit)
            return list(self.session.scalars(query).unique().all())
    
    def get(self, skip: int, limit: int, filters: dict[str, any] | None) -> list[TransferPolicy]:
        query = select(TransferPolicy)
        if filters:
            query = self._filter(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())
