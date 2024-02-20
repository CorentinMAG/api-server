from ..models import TransferRequest, State, Queue
from ..utils.jsontypes import FilterRequestsParams
from ..db import db

def filter_requests(params: FilterRequestsParams):
    
    base = db.session.query(TransferRequest)

    if params.get("state", None)  is not None:
        base = base.filter(State.state == params["state"])

    if params.get("queues", None) is not None:
        queues = params["queues"].split(",")
        for queue in queues:
            base = base.filter(Queue.name == queue)

    base.order_by(Queue.priority)
    base.order_by(TransferRequest.date) 

    return base