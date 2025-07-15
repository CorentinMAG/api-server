"""
Transfer requests API routes with dependency injection.
"""

from __future__ import annotations

from typing import Optional

from dtr_common.constantes import Mode
from dtr_common.schema.requests import (
    CommandedTransferRequestSchema,
    TriggerTransferRequestSchema,
)
from dtr_common.utils import parse_params
from flask import Blueprint, current_app, g, request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import SQLAlchemyError

from api.db import db
from api.repositories import TransferRequestRepository
from api.services.filters import get_params
from api.services.queue_service import QueueService
from api.services.requests import create_commanded_request, create_periodical_requests, update_request
from api.services.validation_service import ValidationService
from api.utils.responses import error_response, success_response
from api.utils.validation import validate_query

bp = Blueprint("requests", __name__)


def _get_request_services():
    """
    Dependency injection helper for request services.

    Returns services with proper database session and logging.
    This enables clean testing and separation of concerns.
    """
    db_session = db.session
    logger = current_app.logger

    transfer_repo = TransferRequestRepository(db_session)
    validation_service = ValidationService(transfer_request_repo=transfer_repo, logger=logger)
    # QueueService expects a TransferRequestRepository, not a db_session
    queue_service = QueueService(transfer_repo, logger=logger)

    return {
        "transfer_repo": transfer_repo,
        "validation_service": validation_service,
        "queue_service": queue_service,
        "logger": logger,
    }


def _build_error_response(message: str, status_code: int = 400) -> tuple:
    """Standardized error response builder."""
    return error_response(message, status_code=status_code)


def _build_success_response(data: dict, status_code: int = 200) -> tuple:
    """Standardized success response builder."""
    return success_response(data, status_code=status_code)


class TransferStatusQuery(BaseModel):
    id: str = Field(..., alias="id")


@bp.route("/get-status", methods=["GET"])
@validate_query(TransferStatusQuery)
def get_transfer_status():
    """
    Get detailed transfer request status information.

    Refactored to use dependency injection and standardized responses.
    """
    try:
        # Service dependency injection
        services = _get_request_services()
        transfer_repo = services["transfer_repo"]
        logger = services["logger"]

        params = get_params()
        if params.mode == Mode.OFFLINE:
            return error_response("system is in OFFLINE mode", status_code=503)

        query: TransferStatusQuery = g.validated_query  # type: ignore[attr-defined]

        # Repository query with injected dependencies
        transfer_request = transfer_repo.filter_by_uid(query.id)

        if not transfer_request:
            return error_response("Transfer request not found", status_code=404)

        # Service layer business logic
        detailed_request = _build_detailed_request_response(transfer_request)
        logger.info(f"Retrieved status for transfer {query.id}")

        return success_response(detailed_request)

    except Exception as e:
        logger.error(f"Error retrieving transfer status: {str(e)}")
        return error_response("internal server error", status_code=500)


def _build_detailed_request_response(transfer_request) -> dict:
    """
    Build detailed transfer request response with business logic separation.

    This helper function encapsulates the response building logic,
    making it testable and maintainable.
    """
    # Get the latest state
    latest_state = transfer_request.states[0] if transfer_request.states else None

    # Calculate transfer rate with error handling
    transfer_rate = _calculate_transfer_rate(transfer_request)

    # Get failure information
    failure_count = transfer_request.nb_retry
    failure_reason = None
    if latest_state and latest_state.failure_reason:
        failure_reason = latest_state.failure_reason

    # Get source and destination information
    source = _build_source_info(transfer_request)
    destination = _build_destination_info(transfer_request)

    return {
        "follows_from_task": transfer_request.follows_from_task,
        "transfer_id": str(transfer_request.uid),
        "transfer_status": {
            "status": latest_state.state.value if latest_state else "UNKNOWN",
            "sub_status": latest_state.sub_state.value if latest_state and latest_state.sub_state else None,
            "failure_count": failure_count,
            "failure_reason": failure_reason,
        },
        "transfer_info": {
            "data_identifier": transfer_request.filename,
            "data_size_mb": transfer_request.size,
            "data_type": "file",
            "policy_name": transfer_request.policy.name if transfer_request.policy else None,
            "created_at": transfer_request.created_at.isoformat() if transfer_request.created_at else None,
            "transfer_begin_time": transfer_request.start.isoformat() if transfer_request.start else None,
            "transfer_end_time": transfer_request.end.isoformat() if transfer_request.end else None,
            "transfer_rate_mb_s": round(transfer_rate, 2) if transfer_rate else None,
        },
        "download": {
            "source": source,
            "download_rate_mb_s": transfer_request.download_rate,
            "download_time_s": transfer_request.download_time,
        },
        "upload": {
            "destination": destination,
            "upload_rate_mb_s": transfer_request.upload_rate,
            "upload_time_s": transfer_request.upload_time,
        },
    }


def _calculate_transfer_rate(transfer_request) -> Optional[float]:
    """Calculate transfer rate with proper error handling."""
    if not (transfer_request.start and transfer_request.end and transfer_request.size):
        return None

    try:
        duration_seconds = (transfer_request.end - transfer_request.start).total_seconds()
        if duration_seconds > 0:
            return transfer_request.size / duration_seconds
    except (TypeError, ValueError):
        pass

    return None


def _build_source_info(transfer_request) -> Optional[dict]:
    """Build source information with null checks."""
    if not (transfer_request.policy and transfer_request.policy.src):
        return None

    src = transfer_request.policy.src
    return {
        "name": src.target.name if src.target else None,
        "path": src.path,
        "protocol": src.target.protocol.value if src.target else None,
    }


def _build_destination_info(transfer_request) -> Optional[dict]:
    """Build destination information with null checks."""
    if not transfer_request.dest:
        return None

    dest = transfer_request.dest
    return {
        "name": dest.target.name if dest.target else None,
        "path": dest.path,
        "protocol": dest.target.protocol.value if dest.target else None,
    }


@bp.route("/request", methods=["POST"])
def new_requests():
    """
    Create new periodical transfer requests.

    Refactored to use dependency injection and validation services.
    """
    try:
        services = _get_request_services()
        validation_service = services["validation_service"]
        logger = services["logger"]
    except Exception as e:
        # Log and return error if service construction fails
        current_app.logger.error("Service initialization failed: %s", str(e), exc_info=True)
        from api.utils.responses import error_response as _er

        return _er("Service initialization failed", status_code=500)

    try:
        payload = request.get_json(silent=True)
        if not payload:
            return _build_error_response("No payload provided", 400)

        # Schema validation with explicit error handling
        try:
            schema = TriggerTransferRequestSchema(**payload)
        except ValidationError:
            return _build_error_response("Invalid payload", 400)

        # Service layer call with dependency injection
        created = create_periodical_requests(schema, logger=logger, validation_service=validation_service)

        if created:
            logger.info("Periodical transfer requests created (%d)", created)
        else:
            logger.debug("No new periodical transfer requests created (duplicates or queue full)")

        return _build_success_response({}, 200)

    except SQLAlchemyError as se:
        logger.error(f"Database error while creating periodical requests: {str(se)}")
        return _build_error_response("Database error", 500)
    except Exception as e:
        logger.error(f"Error creating periodical requests: {str(e)}")
        return _build_error_response("Failed to create transfer requests", 500)


@bp.route("/transfer-request", methods=["POST"])
def new_commanded_request():
    """
    Create new commanded transfer request.

    Refactored with dependency injection and improved error handling.
    """
    try:
        services = _get_request_services()
        validation_service = services["validation_service"]
        logger = services["logger"]
    except Exception as e:
        current_app.logger.error("Service initialization failed: %s", str(e), exc_info=True)
        from api.utils.responses import error_response as _er

        return _er("Service initialization failed", status_code=500)

    try:
        payload = request.get_json(silent=True)
        if not payload:
            return _build_error_response("No payload provided")

        # Schema validation with explicit error handling
        try:
            schema = CommandedTransferRequestSchema(**payload)
        except ValidationError:
            return _build_error_response("Invalid payload", 400)

        # Service layer call with dependency injection
        # Call service layer without unsupported arguments to avoid TypeError
        request_uids, error_message, status_code = create_commanded_request(schema, logger=logger)

        if request_uids:
            logger.info(f"Commanded transfer request created: {request_uids}")
            return _build_success_response({"transfer_id": request_uids})

        return _build_error_response(error_message or "Failed to create transfer request", status_code or 500)

    except SQLAlchemyError as se:
        logger.error(f"Database error while creating commanded request: {str(se)}")
        return _build_error_response("Database error", 500)
    except Exception as e:
        logger.error(f"Error creating commanded request: {str(e)}")
        return _build_error_response("Failed to create transfer request", 500)


@bp.route("/request/<int:id>", methods=["PUT"])
def update_requests(id: int):
    """
    Update transfer request.

    Refactored with dependency injection and validation.
    """
    try:
        services = _get_request_services()
        logger = services["logger"]
    except Exception:
        from api.utils.responses import error_response as _er

        return _er("Service initialization failed", status_code=500)

    try:
        payload = request.json
        if not payload:
            return _build_error_response("No payload provided")

        # Service layer call with dependency injection
        # Call service layer without unsupported arguments to avoid TypeError
        response = update_request(id, payload)

        if response:
            logger.info(f"Transfer request {id} updated successfully")
            return _build_success_response(response)

        return _build_success_response({})

    except Exception as e:
        logger.error(f"Error updating request {id}: {str(e)}")
        return _build_error_response("Failed to update transfer request", 500)


@bp.route("/filter", methods=["GET"])
def filter_requests_route():
    """
    Filter transfer requests with dependency injection.

    Refactored to use repository pattern and validation services.
    """
    try:
        services = _get_request_services()
        transfer_repo = services["transfer_repo"]
        logger = services["logger"]
    except Exception:
        from api.utils.responses import error_response as _er

        return _er("Service initialization failed", status_code=500)

    try:
        # Parameter validation
        params = get_params()
        if params.mode == Mode.OFFLINE:
            return _build_error_response("System is in OFFLINE mode")

        parsed_params = parse_params(request.args.to_dict())

        # Repository query with dependency injection
        requests = transfer_repo.filter_requests(
            id=parsed_params.get("id"),
            states=parsed_params.get("states"),
            sources=parsed_params.get("sources"),
            targets=parsed_params.get("targets"),
            limit=parsed_params.get("limit"),
        )

        logger.info(f"Filtered {len(requests)} transfer requests")
        return _build_success_response({"requests": [req.to_dict() for req in requests]})

    except Exception as e:
        logger.error(f"Error filtering requests: {str(e)}")
        return _build_error_response("Failed to filter transfer requests", 500)
