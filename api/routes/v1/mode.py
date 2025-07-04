"""
Mode and global parameters API routes with dependency injection and error handling.
"""
from __future__ import annotations

from dtr_common.constantes import Mode
from flask import Blueprint, current_app

from api.services.filters import get_params, switch_mode
from api.utils.responses import error_response, success_response

bp = Blueprint("mode", __name__)


def _get_mode_services():
    """
    Dependency injection helper for mode services.

    Returns services with proper database session and logging.
    """
    logger = current_app.logger

    return {"logger": logger}


@bp.route("/offline", methods=["POST"])
def set_offline_mode():
    """
    Set DTR to offline mode.
    """
    try:
        # Service dependency injection
        services = _get_mode_services()
        logger = services["logger"]

        # Service layer call
        switch_mode(Mode.OFFLINE)

        logger.info("System switched to OFFLINE mode")
        return success_response({"message": "System switched to OFFLINE mode"})

    except Exception as e:
        logger.error(f"Error switching to offline mode: {str(e)}")
        return error_response("Failed to switch to offline mode", 500)


@bp.route("/online", methods=["POST"])
def set_online_mode():
    """
    Set DTR to online mode.
    """
    try:
        # Service dependency injection
        services = _get_mode_services()
        logger = services["logger"]

        # Service layer call
        switch_mode(Mode.ONLINE)

        logger.info("System switched to ONLINE mode")
        return success_response({"message": "System switched to ONLINE mode"})

    except Exception as e:
        logger.error(f"Error switching to online mode: {str(e)}")
        return error_response("Failed to switch to online mode", 500)


@bp.route("/global_params", methods=["GET"])
def get_global_parameters():
    """
    Get DTR global parameters.
    """
    try:
        # Service dependency injection
        services = _get_mode_services()
        logger = services["logger"]

        # Service layer call
        params = get_params()

        if params is None:
            logger.warning("No global parameters found")
            return error_response("No global parameters found", 404)

        logger.info("Retrieved global parameters successfully")
        return success_response(params.to_dict())

    except Exception as e:
        logger.error(f"Error retrieving global parameters: {str(e)}")
        return error_response("Failed to get global parameters", 500)
