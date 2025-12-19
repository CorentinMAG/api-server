from __future__ import annotations
from flask import Blueprint, request

from api.utils.utils import check_gparams_before_request, custom_app

bp = Blueprint("worker", __name__)

@bp.before_request
def handler():
    check_gparams_before_request()

@bp.route("/configuration/worker", methods=["GET"])
def worker():
    """
    Get next available transfer request for a worker to process

    Args:
      None explicitly. Query parameters are taken from `request.args`:
        size (int, optional): worker size
        id   (str, optional): worker identifier or default
    Returns:
      flask.Response: A JSON response containing:
        request (dict): JSON representation of the TransferRequest object
    """
    app = custom_app()

    size = request.args.get("size", type=int, default=1_000_000)
    worker_id = request.args.get("id", type=str, default="default")


    worker = app.services.workers.get_by_name(worker_id)
    nrequest = app.services.requests.get_next_worker_request(size, worker = worker)

    if nrequest:
        nrequest = app.services.requests.start_processing(nrequest.id)
        app.logger.info(f"Assigned transfer request {nrequest.uid} to worker")
        return {"request": nrequest.to_dict(rules=("policy.src", "policy.name", "policy.parameters", "nb_retry"))}

    # No request was found. No need to commit anything.
    app.logger.debug("No available transfer requests for worker %s", worker_id)
    return {"request": {}}
