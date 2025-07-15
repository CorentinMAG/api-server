"""
Worker API routes with dependency injection and error handling.
"""

from __future__ import annotations

import datetime
import logging

from dtr_common.constantes import Mode, State as StateEnum
from flask import Blueprint, current_app, request
from sqlalchemy.exc import SQLAlchemyError

from api.db import db
from api.models import State
from api.services.filters import get_params
from api.services.requests import get_next_request
from api.utils.responses import error_response, success_response

bp = Blueprint("worker", __name__)


def _get_logger():
    """Get logger with fallback for test environments."""
    try:
        return current_app.logger
    except RuntimeError:
        return logging.getLogger(__name__)


@bp.route("/configuration/worker", methods=["GET"])
def worker():
    """
    Get next available transfer request for worker processing.
    This endpoint ensures atomicity by using a transaction with row-level locking
    (SELECT ... FOR UPDATE) to prevent the same task from being assigned to
    multiple workers simultaneously.
    """
    logger = _get_logger()
    try:
        ngparams = get_params()
        if ngparams is None or ngparams.mode == Mode.OFFLINE:
            logger.info("Worker configuration request in OFFLINE mode, no request assigned.")
            return success_response({"request": None})

        worker_storage = request.args.get("size", type=float)
        if worker_storage is not None and worker_storage <= 0:
            return error_response("Worker storage size must be positive", 400)

        # The transaction is implicitly managed by Flask-SQLAlchemy per request.
        # We perform all operations within this single request context.
        params = {"size": worker_storage, "state": StateEnum.QUEUED}
        next_request = get_next_request(params, db_session=db.session)

        if next_request:
            # This all happens before the transaction is committed.
            # The row remains locked until the commit.
            nstate = State(state=StateEnum.IN_PROGRESS)
            next_request.states.append(nstate)
            next_request.start = datetime.datetime.now(datetime.timezone.utc)

            db.session.flush()

            # The request object is still bound to the session, so we can serialize it.
            response_data = next_request.to_dict()

            # Commit the transaction to finalize the state change and release the lock.
            db.session.commit()

            logger.info(f"Assigned transfer request {next_request.uid} to worker")
            return success_response({"request": response_data})

        # No request was found. No need to commit anything.
        logger.debug("No available transfer requests for worker")
        return success_response({"request": None})

    except SQLAlchemyError as e:
        logger.error(f"Database error while getting worker configuration: {e}", exc_info=True)
        db.session.rollback()
        return error_response("Database error during worker configuration", 500)
    except Exception as e:
        logger.error(f"Unexpected error in worker configuration: {e}", exc_info=True)
        db.session.rollback()
        return error_response("Failed to get worker configuration", 500)
