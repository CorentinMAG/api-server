from common.types.filter import FilterPolicyParams

from ..db import db
from ..models import (
    DestinationPolicy,
    Queue,
    SourcePolicy,
    Target,
    TransferParameters,
    TransferPolicy,
)


def filter_policies(params: FilterPolicyParams):
    base = db.session.query(TransferPolicy)

    if params.get("enabled") is not None:
        base = base.filter(TransferPolicy.enabled == params["enabled"])
    if params.get("dataType", None) is not None:
        base = base.filter(TransferParameters.data_type == params["dataType"])
    if params.get("type") is not None:
        base = base.filter(TransferPolicy.type == params["type"])
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
    base.order_by(TransferPolicy.created_at)

    return base
