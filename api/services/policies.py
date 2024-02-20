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
        base = base.join(TransferPolicy.queues).filter(Queue.name.in_(queues))
    base.order_by(TransferPolicy.created_at)
    
    return base
