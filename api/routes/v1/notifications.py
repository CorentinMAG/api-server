"""
Notifications API routes with dependency injection and error handling.
"""

from __future__ import annotations

from dtr_common.constantes import Mode, SubState
from flask import Blueprint, current_app

from api.services.filters import get_params
from api.services.requests import get_next_request
from api.utils.responses import error_response, success_response

bp = Blueprint("notification", __name__)


def _get_notification_services():
    """
    Dependency injection helper for notification services.

    Returns services with proper database session and logging.
    """
    logger = current_app.logger

    return {"logger": logger}


@bp.route("/notifications", methods=["GET"])
def notification():
    """
    Get next transfer request requiring notification.
    """
    try:
        # Service dependency injection
        services = _get_notification_services()
        logger = services["logger"]

        # Parameter validation
        ngparams = get_params()
        if ngparams is None or ngparams.mode == Mode.OFFLINE:
            logger.info("Notification request in OFFLINE mode")
            return success_response({"request": None})

        # Service layer call with dependency injection
        params = {"sub_state": SubState.NOTIFY}
        nrequest = get_next_request(params)

        if nrequest is not None:
            logger.info(f"Retrieved notification request {nrequest.uid}")
            return success_response({"request": nrequest.to_dict()})

        logger.debug("No transfer requests requiring notification")
        return success_response({"request": None})

    except Exception as e:
        logger.error(f"Error retrieving notification request: {str(e)}")
        return error_response("Failed to get notification request", 500)
