from .base import BaseRepository
from ..models import Trigger, TransferPolicy
from ..errors import NotFoundError
from sqlalchemy import select, func, Select
from typing import NamedTuple
from flask_sqlalchemy import SQLAlchemy

class ITriggerPaginate(NamedTuple):
    page: int
    per_page: int
    pages: int
    total: int
    items: list[TransferPolicy]

class TriggerRepository(BaseRepository[Trigger]):
    def __init__(self, db: SQLAlchemy):
        super().__init__(Trigger, db)

    def get_by_name(self, name: str) -> Trigger:
        query = (
            select(Trigger)
            .where(Trigger.name == name)
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"Trigger with name {name} not found")
        return obj

    def get_policies(self, query: Select, page: int = 1, page_size: int = 100) -> ITriggerPaginate:
        total = self.session.scalar(select(func.count()).select_from(query.subquery()))
        pages = 1 if total < page_size else total // page_size  
        items: list[TransferPolicy] = self.session.scalars(
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return ITriggerPaginate(
            page=page, 
            per_page=page_size, 
            pages=pages, 
            total = total, 
            items = items
        )