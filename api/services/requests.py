from ..models import TransferRequest, State, Queue, TransferPolicy
from common.jsontypes import FilterRequestsParams
from typing import cast
from flask import current_app as app
from common.constantes import State as StateEnum
from ..db import db

def filter_requests(params: FilterRequestsParams):
    base = (
        db.session
        .query(TransferRequest)
        .join(Queue)
        .order_by(Queue.priority.desc())
        .order_by(TransferRequest.date.asc())
        )

    if params.get("state", None)  is not None:
        base = base.filter(State.state == params["state"])

    if params.get("queues", None) is not None:
        queues = params["queues"].split(",")
        base = base.filter(Queue.name.in_(queues))

    return base

def create_request(policy_id: int, files: list[str]) -> None:
    npolicy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
    if npolicy is not None:
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

        npolicy.transfers.extend(nrequests)
        db.session.commit()
    else:
        app.logger.error("policy id: %d doesn't exist", policy_id)