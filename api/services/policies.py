from ..models import TransferPolicy, TransferParameters, Target, SourcePolicy, DestinationPolicy, Queue
from common.jsontypes import FilterPolicyParams
from ..db import db

def filter_policies(params: FilterPolicyParams):

    base = db.session.query(TransferPolicy)

    if params.get("enabled", None) is not None:
        base = base.filter(TransferPolicy.enabled == params["enabled"])
    if params.get("dataType", None) is not None:
        base = base.filter(TransferParameters.data_type == params["dataType"])
    if params.get("type", None) is not None:
        base = base.filter(TransferPolicy.type == params["type"])
    if params.get("src", None) is not None:
        base = base.join(SourcePolicy).join(Target).filter(Target.name == params["src"])
    if params.get("dest", None) is not None:
        base = base.join(DestinationPolicy).join(Target).filter(Target.name == params["dest"])
    if params.get("queues", None) is not None:
        queues = params["queues"].split(",")
        base = base.join(TransferPolicy.queue).filter(Queue.name.in_(queues))
    if params.get("id", None) is not None:
        base = base.filter(TransferPolicy.id == params["id"])
    if params.get("ids", None) is not None:
        policies_id = params["ids"].split(",")
        policies_id = map(lambda i: int(i), policies_id)
        base = base.filter(TransferPolicy.id.in_(policies_id))
    base.order_by(TransferPolicy.created_at)
    
    return base
