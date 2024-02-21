from ..models import TransferRequest, State, Queue
from common.jsontypes import FilterRequestsParams
from typing import cast
from common.constantes import State as StateEnum
from ..db import db
from ..repositories import tr_repository

def filter_requests(params: FilterRequestsParams):
    base = db.session.query(TransferRequest)

    if params.get("state", None)  is not None:
        base = base.filter(State.state == params["state"])

    if params.get("queues", None) is not None:
        queues = params["queues"].split(",")
        base = base.filter(Queue.name.in_(queues))

    base.order_by(Queue.priority)
    base.order_by(TransferRequest.date) 

    return base

def create_request(policy_id: int, files: list[str]) -> None:
    npolicy = tr_repository.get_by_id(policy_id)
    nqueue = cast(Queue, npolicy.queue)

    nrequests = []

    for file in files:
        nstate = State(state = StateEnum.QUEUED.value)
        nrequest = TransferRequest(
            filename = file,
            states = [nstate],
            queue = nqueue
            )
        nrequests.append(nrequest)

    npolicy.transfers.extend(nrequest)
    db.session.commit()