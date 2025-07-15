"""
Configuration API routes with dependency injection and error handling.
"""
from __future__ import annotations

from dtr_common.schema import ConfigurationSchema
from flask import Blueprint, current_app as app, request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from api.services.configuration import configure as set_configuration, unconfigure as del_configuration
from api.utils.responses import error_response, success_response

bp = Blueprint("configuration", __name__)


@bp.route("/configure", methods=["POST"])
def configure():
    """
    delete the previous configuration and apply a new one
    """
    payload = request.get_json(silent=True)

    if not payload:
        return error_response("No payload provided", status_code=400)

    # Validate payload structure
    try:
        configuration = ConfigurationSchema(**payload)
    except ValidationError as e:
        app.logger.error("Invalid configuration payload: %s", e)
        return error_response("Invalid configuration", status_code=400, details=e.errors())

    # Apply new configuration inside transactional service call
    try:
        del_configuration(keep=["transfer_requests", "global_parameters", "states"])
        set_configuration(configuration)
        app.logger.info("New configuration has been successfully applied")
        return success_response({"message": "configuration has been applied"}, status_code=201)
    except SQLAlchemyError:
        # Already logged inside service layer
        return error_response("Database error while applying configuration", status_code=500)
    except Exception as e:
        app.logger.error("Unexpected error while applying configuration: %s", e, exc_info=True)
        return error_response("Internal server error", status_code=500)


@bp.route("/configure", methods=["DELETE"])
def unconfigure():
    """
    delete all records from all tables in the database
    we can specify in the body if we want to delete all transfer requests
    """
    try:
        del_configuration(keep=["transfer_requests"])
        app.logger.info("configuration has been successfully deleted")
        return success_response({"message": "configuration has been deleted"})
    except SQLAlchemyError:
        return error_response("Database error while deleting configuration", status_code=500)
    except Exception as e:
        app.logger.error("Unexpected error while deleting configuration: %s", e, exc_info=True)
        return error_response("Internal server error", status_code=500)
