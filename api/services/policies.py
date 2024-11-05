from sqlalchemy import or_
from api.db import db
from api.models import (
    DestinationPolicy,
    Queue,
    SourcePolicy,
    Target,
    TransferPolicyParameters,
    TransferPolicy,
    PeriodicalParameters,
)
import datetime
from typing import cast, TypedDict
from dtr_common.constantes import Type


class FilterPolicyParams(TypedDict, total=False):
    enabled: bool
    type: Type | str
    src: str
    dest: str
    queues: str
    id: int
    ids: str
    next_polling_min_time: bool


def filter_policies(params: FilterPolicyParams):
    base = db.session.query(TransferPolicy)

    if params.get("enabled") is not None:
        base = base.filter(TransferPolicy.enabled == params["enabled"])
    if params.get("type") is not None:
        type = params["type"] if isinstance(params["type"], Type) else Type[params["type"].upper()]
        base = base.filter(TransferPolicy.type == type)
    if params.get("src") is not None:
        base = base.join(SourcePolicy).join(Target).filter(Target.name == params["src"])
    if params.get("dest") is not None:
        base = base.join(DestinationPolicy).join(Target).filter(Target.name == params["dest"])
    if params.get("queues") is not None:
        queues = params["queues"].split(",")
        base = base.join(TransferPolicy.queue).filter(Queue.name.in_(queues))
    if params.get("id") is not None:
        base = base.filter(TransferPolicy.id == params["id"])
    if params.get("ids") is not None:
        policies_id = params["ids"].split(",")
        policies_id = map(lambda i: int(i), policies_id)
        base = base.filter(TransferPolicy.id.in_(policies_id))
    if params.get("next_polling_min_time") is not None and params.get("next_polling_min_time") is True:
        base = (
            base.join(TransferPolicyParameters)
            .join(PeriodicalParameters)
            .filter(
                or_(
                    PeriodicalParameters.next_polling_min_time.is_(None),
                    PeriodicalParameters.next_polling_min_time
                    <= datetime.datetime.now(datetime.timezone.utc),
                )
            )
        )
    base.order_by(TransferPolicy.created_at)

    return base


def update_policy(policy_id: int, payload: dict):
    npolicy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
    if npolicy:
        npolicy.update(payload)
        db.session.commit()
