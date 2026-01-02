from .base import BaseRepository
from api.models import (
    TransferPolicy,
    DestinationPolicy,
    DestinationPolicy,
)
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select
from api.exceptions import NotFoundException
from typing import overload


class TransferPolicyRepository(BaseRepository[TransferPolicy]):

    def get_by_name(self, name: str) -> TransferPolicy:
        """get transfer policy by name"""

        query = select(TransferPolicy).where(TransferPolicy.name == name)
        obj = self.session.scalar(query)

        if not obj:
            raise NotFoundException(f"TransferPolicy with name {name} not found")
        return obj

    @overload
    def get_with_relations(self, id: int) -> TransferPolicy: ...

    @overload
    def get_with_relations(
        skip: int | None = None,
        limit: int | None = None,
        filters: dict[str, any] | None = None,
    ) -> list[TransferPolicy]: ...

    def get_with_relations(
        self,
        id: int | None = None,
        skip: int | None = None,
        limit: int | None = None,
        filters: dict[str, any] | None = None,
    ) -> TransferPolicy | list[TransferPolicy]:
        """get transfer policy with all relations"""

        query = select(TransferPolicy).options(
            selectinload(TransferPolicy.dests).joinedload(DestinationPolicy.target),
            selectinload(TransferPolicy.dests).selectinload(
                DestinationPolicy.notifications
            ),
            joinedload(TransferPolicy.parameters),
            joinedload(TransferPolicy.queue),
        )

        if id is not None:
            query = query.where(TransferPolicy.id == id)
            obj = self.session.scalar(query)
            if not obj:
                raise NotFoundException(f"TransferPolicy with id {id} not found")
            return obj
        else:
            if filters:
                self.filters(query, filters)
            query = query.offset(skip).limit(limit)
            return list(self.session.scalars(query).unique().all())

    def get(
        self, skip: int, limit: int, filters: dict[str, any] | None
    ) -> list[TransferPolicy]:

        query = select(TransferPolicy)
        if filters:
            self.filters(query, filters)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())
