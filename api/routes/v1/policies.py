"""
Transfer policies API routes with dependency injection.
"""
from __future__ import annotations

from typing import cast

from dtr_common.constantes import Mode
from dtr_common.utils import parse_params
from flask import Blueprint, current_app, request

from api.db import db
from api.models import TransferPolicy
from api.repositories import TransferPolicyRepository
from api.services.configuration import create_policies
from api.services.filters import get_params
from api.services.policies import filter_policies, update_policy
from api.services.validation_service import ValidationService
from api.utils.responses import error_response, success_response

bp = Blueprint("policies", __name__)


def _get_policy_services():
    """
    Dependency injection helper for policy services.

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

@bp.route("/policies", methods=["GET"])
def policies():
    """
    List all transfer policies with filtering and pagination.

    Query params:
    - id: int
    - ids: str
    - type: periodical / commanded
    - dataType: file / folder
    - enabled: true / false
    - queues: name1,name2,...
    - src: source filter
    - dest: destination filter
    """
    services = _get_policy_services()
    logger = services["logger"]

    try:
        # Parameter validation
        ngparams = get_params()
        if ngparams is None or ngparams.mode == Mode.OFFLINE:
            logger.warning("Policies request in OFFLINE mode")
            return success_response({"policies": [], "page": 0, "page_size": 0, "total": -1},)

        # Pagination parameters
        page = request.args.get("page", type=int, default=1)
        page_size = request.args.get("page_size", type=int, default=10)
        parsed_params = parse_params(request.args.to_dict())

        # Service layer call with dependency injection
        query = filter_policies(parsed_params)

        # Database pagination
        result = db.paginate(query, page=page, per_page=page_size)
        policies = cast(list[TransferPolicy], result.items)

        response_data = {
            "policies": [p.to_dict() for p in policies],
            "page": page,
            "page_size": page_size,
            "total": result.total,
        }

        logger.info(f"Retrieved {len(policies)} policies (page {page})")
        return success_response(response_data)

    except Exception as e:
        logger.error(f"Error retrieving policies: {str(e)}")
        return error_response("Failed to retrieve policies", 500)


@bp.route("/policies", methods=["POST"])
def post_policies():
    """
    Create new transfer policies.
    """
    services = _get_policy_services()
    logger = services["logger"]

    try:
        payload = request.json
        if not payload or "policies" not in payload:
            return error_response("No policies provided in payload")

        policies_data = payload["policies"]
        if not isinstance(policies_data, list):
            return error_response("Policies must be a list")

        # Service layer call
        create_policies(policies_data)

        logger.info(f"Created {len(policies_data)} policies successfully")
        return success_response("Policies created successfully", 200)

    except Exception as e:
        logger.error(f"Error creating policies: {str(e)}")
        return error_response("Failed to create policies", 500)


@bp.route("policies/<int:id>", methods=["PUT"])
def put_policy(id: int):
    """
    Update a transfer policy.
    """
    services = _get_policy_services()
    policy_repo = services["policy_repo"]
    logger = services["logger"]

    try:
        payload = request.json
        if not payload:
            return error_response("No payload provided")

        # Verify policy exists
        existing_policy = policy_repo.get_by_id(id)
        if not existing_policy:
            return error_response("Policy not found", 404)

        # Service layer call
        update_policy(id, payload)

        logger.info(f"Policy {id} updated successfully")
        return success_response("Policy updated successfully", 200)

    except Exception as e:
        logger.error(f"Error updating policy {id}: {str(e)}")
        return error_response("Failed to update policy", 500)
