from typing import cast

from dtr_common.constantes import State as StateEnum
from dtr_common.types.filter import FilterRequestParams
from flask import current_app as app

from ..db import db
from ..models import Queue, State, TransferPolicy, TransferRequest


def filter_requests(params: FilterRequestParams):
    base = (
        db.session.query(TransferRequest)
        .join(TransferPolicy)
        .join(Queue)
        .join(State)
        .order_by(Queue.priority.desc())
        .order_by(TransferRequest.created_at.asc())
    )

    if params.get("state") is not None:
        base = base.filter(TransferRequest.last_state == params["state"].upper())
    if params.get("states") is not None:
        states = list(map(lambda x: x.upper(), params["states"].split(",")))
        base = base.filter(TransferRequest.last_state.in_(states))

    if params.get("queues") is not None:
        queues = params["queues"].split(",")
        base = base.filter(Queue.name.in_(queues))

    return base


def create_request(policy_id: int, files: list[str]) -> None:
    npolicy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
    if npolicy is not None:
        nrequests: list[TransferRequest] = []

        for file in files:
            # checked nb items in the queue, if the queue is full do not create policy
            nstate = State(state=StateEnum.QUEUED)
            nrequest = TransferRequest(filename=file, states=[nstate])
            nrequests.append(nrequest)     
        npolicy.transfers.extend(nrequests)
        db.session.commit()
        for nrequest in nrequests:
            app.logger.info("[%s] request has been created", nrequest.uid)
    else:
        app.logger.error("policy id: %d doesn't exist", policy_id)
        raise Exception(" policy does not exists") # create class to format exception


def update_request(
    request_id: int,
    status: StateEnum,
    reason: str | None = None,
) -> None:
    nstates  = []
    nrequest = cast(TransferRequest, db.session.query(TransferRequest).get(request_id))

    if status == StateEnum.FAILED and nrequest.policy.parameters.max_retry == nrequest.nb_retry:
        nstate = State(state=StateEnum.CANCELLED, reason="Too many failed attempt")
        nstates.append(nstate)
    elif status == StateEnum.FAILED and nrequest.policy.parameters.max_retry > nrequest.nb_retry:
        nstate_failed = State(state=StateEnum.FAILED, reason=reason)
        nstate_queued = State(state=StateEnum.QUEUED)
        nstates.extend([nstate_failed, nstate_queued])
    else:
        nstate = State(state=status, reason=reason)
        nstates.append(nstate)
    
    nrequest.states.extend(nstates)
    db.session.commit()
    app.logger.info("[%s] request has been updated to state %s", nrequest.uid, nrequest.last_state)


