"""
Notifications API routes with dependency injection and error handling.
"""

from __future__ import annotations

from dtr_common.constantes import Mode, SubState
from flask import Blueprint, current_app

from api.services.filters import get_params
from api.services.requests import get_next_request

bp = Blueprint("notification", __name__)

@bp.route("/notifications", methods=["GET"])
def notification():
    """
    Get next transfer request requiring notification.
    """
    # Parameter validation
    ngparams = get_params()
    if ngparams is None or ngparams.mode == Mode.OFFLINE:
        current_app.logger.info("Notification request in OFFLINE mode")
        return {"request": {}}

    params = {"sub_state": SubState.NOTIFY}
    nrequest = get_next_request(params)

    if nrequest is not None:
        return {"request": nrequest.to_dict()}

    return {"request": {}}
