from __future__ import annotations

from typing import TypedDict, cast

from dtr_common.constantes import Type
from sqlalchemy import select

from api.models import db
from api.models import (
    DestinationPolicy,
    Queue,
    SourcePolicy,
    Target,
    TransferPolicy,
    Trigger
)

from .utils import db_retry, transactional


class FilterPolicyParams(TypedDict, total=False):
    enabled: bool
    type: Type | str
    src: str
    dests: str
    queues: str
    id: int
    ids: str
    next_polling_min_time: bool


@db_retry(total=3, backoff=5)
def filter_policies(params: FilterPolicyParams):
    """Return a SQLAlchemy query filtered according to *params*."""

    base = select(TransferPolicy)

    if params.get("enabled") is not None:
        base = base.where(TransferPolicy.enabled == params["enabled"])
    if params.get("type") is not None:
        type = params["type"] if isinstance(params["type"], Type) else Type[params["type"].upper()]
        base = base.where(TransferPolicy.type == type)
    if params.get("src") is not None:
        base = base.join(SourcePolicy).join(Target).where(Target.name == params["src"])
    if params.get("dests") is not None:
        base = base.join(DestinationPolicy).join(Target).where(Target.name == params["dests"])
    if params.get("queues") is not None:
        queues = params["queues"].split(",")
        base = base.join(TransferPolicy.queue).where(Queue.name.in_(queues))
    if params.get("id") is not None:
        base = base.where(TransferPolicy.id == params["id"])
    if params.get("ids") is not None:
        policies_id = params["ids"].split(",")
        policies_id = map(lambda i: int(i), policies_id)
        base = base.where(TransferPolicy.id.in_(policies_id))
    if params.get("trigger") is not None:
        base = (
            base.
            join(Trigger).
            where(Trigger.name == params["trigger"])
        )
    base = base.order_by(TransferPolicy.created_at)

    return base


@transactional
def update_policy(policy_id: int, payload: dict):
    npolicy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
    if not npolicy:
        from flask import current_app

        current_app.logger.error("TransferPolicy %s not found for update", policy_id)
        return
    npolicy.update(payload)