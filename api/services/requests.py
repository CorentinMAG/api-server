from typing import Literal, cast

from common.constantes import State as StateEnum
from common.types.filter import FilterRequestParams
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
        base = base.filter(TransferRequest.last_state == params["state"])

    if params.get("queues") is not None:
        queues = params["queues"].split(",")
        base = base.filter(Queue.name.in_(queues))

    return base


def create_request(policy_id: int, files: list[str]) -> None:
    npolicy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
    if npolicy is not None:
        nrequests: list[TransferRequest] = []

        for file in files:
            nstate = State(state=StateEnum.QUEUED.value)
            nrequest = TransferRequest(filename=file, states=[nstate])
            nrequests.append(nrequest)

        npolicy.transfers.extend(nrequests)
        db.session.commit()
        for nrequest in nrequests:
            app.logger.info("[%s] request has been created", nrequest.uid)
    else:
        app.logger.error("policy id: %d doesn't exist", policy_id)


def update_request(
    request_id: int,
    status: Literal["queued", "in_progress", "completed", "failed", "notify"],
    reason: str | None = None,
) -> None:
    nrequest = cast(TransferRequest, db.session.query(TransferRequest).get(request_id))
    nstate = State(state=status, reason=reason)
    app.logger.info("[%s] request has been updated to state %s", nrequest.uid, status)
    nrequest.states.append(nstate)
    db.session.commit()
