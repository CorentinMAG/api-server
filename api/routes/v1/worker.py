"""
Worker API routes with dependency injection and error handling.
"""
from __future__ import annotations

import datetime

from dtr_common.constantes import Mode, State as StateEnum
from flask import Blueprint, current_app, request

from api.db import db
from api.models import State
from api.repositories import TransferRequestRepository
from api.services.filters import get_params
from api.services.requests import get_next_request
from api.utils.responses import error_response, success_response

bp = Blueprint("worker", __name__)


def _get_worker_services():
    """
    Dependency injection helper for worker services.

    Returns services with proper database session and logging.
    """
    db_session = db.session
    logger = current_app.logger

    transfer_repo = TransferRequestRepository(db_session)

    return {"transfer_repo": transfer_repo, "logger": logger, "db_session": db_session}


@bp.route("configuration/worker", methods=["GET"])
def worker():
    """
    Get next available transfer request for worker processing.

    Query parameters:
    - size: float - Worker storage capacity in MB
    """
    try:
        # Service dependency injection
        services = _get_worker_services()
        logger = services["logger"]
        db_session = services["db_session"]

        # Parameter validation
        ngparams = get_params()
        if ngparams is None or ngparams.mode == Mode.OFFLINE:
            logger.info("Worker configuration request in OFFLINE mode")
            return success_response({"request": None})

        # Extract worker storage parameter
        worker_storage = request.args.get("size", type=float)
        if worker_storage is not None and worker_storage <= 0:
            return error_response("Worker storage size must be positive", 400)

        # Service layer call with dependency injection
        params = {"size": worker_storage, "state": StateEnum.QUEUED}
        next_request = get_next_request(params)

        if next_request is not None:
            # Update request state to IN_PROGRESS
            nstate = State(state=StateEnum.IN_PROGRESS)
            next_request.states.append(nstate)
            next_request.start = datetime.datetime.now(datetime.timezone.utc)

            # Commit transaction
            db_session.commit()

            logger.info(f"Assigned transfer request {next_request.uid} to worker")
            return success_response({"request": next_request.to_dict()})

        logger.debug("No available transfer requests for worker")
        return success_response({"request": None})

    except Exception as e:
        logger.error(f"Error in worker configuration: {str(e)}")
        return error_response("Failed to get worker configuration", 500)
