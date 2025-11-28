"""
Worker API routes with dependency injection and error handling.
"""

from __future__ import annotations

import datetime

from dtr_common.constantes import Mode, State as StateEnum
from flask import Blueprint, current_app, request

from api.models import db
from api.models import State
from api.services.filters import get_params
from api.services.requests import get_next_request

bp = Blueprint("worker", __name__)

@bp.route("/configuration/worker", methods=["GET"])
def worker():
    """
    Get next available transfer request for worker processing.
    This endpoint ensures atomicity by using a transaction with row-level locking
    (SELECT ... FOR UPDATE) to prevent the same task from being assigned to
    multiple workers simultaneously.

    Query parameters:
    - size: int - worker's data partition size in MB
    """
    ngparams = get_params()
    if ngparams is None or ngparams.mode == Mode.OFFLINE:
        current_app.logger.info("API in OFFLINE mode, no request assigned.")
        return {"request": {}}

    size = request.args.get("size", type=int)
    worker_id = request.args.get("id", type=str, default="default")

    # a worker can only process files whose size is 
    # <= 5% of the worker maximal capacity
    size = int(size * (1 - (5/100)))

    # we format the size in bytes
    size = size * 1024 *1024

    params = {"size": size, "state": StateEnum.QUEUED, "id": worker_id}
    next_request = get_next_request(params)

    if next_request:
        # This all happens before the transaction is committed.
        # The row remains locked until the commit.
        nstate = State(state=StateEnum.IN_PROGRESS)
        next_request.states.append(nstate)
        next_request.start = datetime.datetime.now(datetime.timezone.utc)

        db.session.commit()

        current_app.logger.info(f"Assigned transfer request {next_request.uid} to worker")
        return {"request": next_request.to_dict(rules=("policy.src", "policy.name", "policy.parameters", "nb_retry"))}

    # No request was found. No need to commit anything.
    current_app.logger.debug("No available transfer requests for worker")
    return {"request": {}}
