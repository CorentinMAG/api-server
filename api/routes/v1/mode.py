"""
Mode and global parameters API routes with dependency injection and error handling.
"""
from __future__ import annotations

from dtr_common.constantes import Mode
from flask import Blueprint, current_app

from api.services.filters import get_params, switch_mode

bp = Blueprint("mode", __name__)

@bp.route("/offline", methods=["POST"])
def set_offline_mode():
    """
    Set DTR to offline mode.
    """
    switch_mode(Mode.OFFLINE)
    return {"message": "mode OFFLINE"}



@bp.route("/online", methods=["POST"])
def set_online_mode():
    """
    Set DTR to online mode.
    """
    switch_mode(Mode.ONLINE)
    return {"message": "mode ONLINE"}


@bp.route("/global_params", methods=["GET"])
def get_global_parameters():
    """
    Get DTR global parameters.
    """
    params = get_params()
    logger = current_app.logger

    if params is None:
        logger.error("No global parameters found")
        return {"error": "No global parameters"}, 404

    logger.info("Retrieved global parameters successfully")
    return params.to_dict()

