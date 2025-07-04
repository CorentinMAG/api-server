"""
Configuration API routes with dependency injection and error handling.
"""
from __future__ import annotations

from dtr_common.schema import ConfigurationSchema
from flask import Blueprint, current_app, request
from sqlalchemy.exc import SQLAlchemyError

from api.db import db
from api.repositories import TransferPolicyRepository
from api.services.configuration import configure as set_configuration, unconfigure as del_configuration
from api.services.validation_service import ValidationService
from api.utils.responses import error_response, success_response

bp = Blueprint("configuration", __name__)


def _get_configuration_services():
    """
    Dependency injection helper for configuration services.

    Returns services with proper database session and logging.
    """
    db_session = db.session
    logger = current_app.logger

    policy_repo = TransferPolicyRepository(db_session)
    validation_service = ValidationService(db_session=db_session, logger=logger)

    return {
        "policy_repo": policy_repo,
        "validation_service": validation_service,
        "logger": logger,
        "db_session": db_session,
    }


def _build_error_response(message: str, status_code: int = 400) -> tuple:
    """Standardized error response builder."""
    return error_response(message, status_code=status_code)


def _build_success_response(data: dict, status_code: int = 200) -> tuple:
    """Standardized success response builder."""
    return success_response(data, status_code=status_code)


@bp.route("/configure", methods=["POST"])
def configure():
    """
    Delete the previous configuration and apply a new one.
    """
    try:
        # Service dependency injection
        services = _get_configuration_services()
        logger = services["logger"]

        # Payload validation
        payload = request.json
        if not payload:
            return _build_error_response("No configuration payload provided", 400)

        # Schema validation
        try:
            configuration = ConfigurationSchema(**payload)
        except Exception as e:
            logger.error(f"Configuration schema validation failed: {str(e)}")
            return _build_error_response(f"Invalid configuration schema: {str(e)}", 400)

        # Clear previous configuration (keep essential data)
        del_configuration(keep=["transfer_requests", "global_parameters", "states"])
        logger.info("Previous configuration cleared")

        # Apply new configuration
        set_configuration(configuration)

        logger.info("New configuration applied successfully")
        return _build_success_response({"message": "configuration has been applied"}, 201)

    except SQLAlchemyError as e:
        logger.error(f"Database error during configuration: {str(e)}")
        return _build_error_response("Database error during configuration", 500)
    except Exception as e:
        logger.error(f"Unexpected error during configuration: {str(e)}")
        return _build_error_response("Failed to apply configuration", 500)


@bp.route("/configure", methods=["DELETE"])
def unconfigure():
    """
    Delete all records from all tables in the database.
    """
    try:
        # Service dependency injection
        services = _get_configuration_services()
        logger = services["logger"]

        # Parse request body for options (optional)
        # Handle cases where request.json might raise an exception
        try:
            payload = request.json or {}
        except Exception:
            payload = {}

        keep_transfers = payload.get("keep_transfer_requests", True)

        # Determine what to keep during unconfiguration
        keep_list = ["transfer_requests"] if keep_transfers else []

        # Service layer call
        del_configuration(keep=keep_list)

        logger.info(f"Configuration deleted (kept: {keep_list})")
        return _build_success_response({"message": "configuration has been deleted"}, 200)

    except SQLAlchemyError as e:
        logger.error(f"Database error during unconfiguration: {str(e)}")
        return _build_error_response("Database error during unconfiguration", 500)
    except Exception as e:
        logger.error(f"Unexpected error during unconfiguration: {str(e)}")
        return _build_error_response("Failed to delete configuration", 500)
