from typing import Generic, TypeVar, Protocol
from ..models import Trigger, TransferPolicy
from ..models import db
from sqlalchemy import select
from dtr_common.constantes import Type

T = TypeVar("T")

class ITriggerPaginate(Protocol, Generic[T]):
    page: int
    per_page: int
    pages: int
    total: int
    items: list[TransferPolicy]

def get_trigger(name: str) -> Trigger:
    stmt = select(Trigger).where(Trigger.name == name)
    trigger = db.session.execute(stmt).scalar()
    if trigger:
        return trigger
    raise ValueError(f"Trigger with name {name} doesn't exist")

def get_paginated_policies(name: str, page: int, page_size: int) -> ITriggerPaginate:
    stmt = (
        select(TransferPolicy)
        .outerjoin(Trigger)
        .where(
            TransferPolicy.enabled == True,
            TransferPolicy.type == Type.PERIODICAL
        )
    )
    if name == "default":
        stmt = stmt.where(TransferPolicy.trigger_id.is_(None))
    else:
        stmt = stmt.where(Trigger.name == name)
    return db.paginate(stmt, page = page, per_page=page_size)