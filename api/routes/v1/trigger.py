"""
Trigger API routes with dependency injection and error handling.
"""
from __future__ import annotations

from typing import cast

from dtr_common.constantes import Mode, Type
from flask import Blueprint, current_app, request

from api.db import db
from api.models import TransferPolicy
from api.repositories import TransferPolicyRepository
from api.services.filters import get_params
from api.services.policies import filter_policies
from api.utils.responses import error_response, success_response

bp = Blueprint("trigger", __name__)


def _get_trigger_services():
    """
    Dependency injection helper for trigger services.

    Returns services with proper database session and logging.
    """
    db_session = db.session
    logger = current_app.logger

    policy_repo = TransferPolicyRepository(db_session)

    return {"policy_repo": policy_repo, "logger": logger, "db_session": db_session}


@bp.route("/configuration/trigger", methods=["GET"])
def trigger():
    """
    Get trigger configuration - all activated periodical transfer policies.

    Query parameters:
    - page: int - Page number for pagination (default: 1)
    - page_size: int - Items per page (default: 10)
    """
    try:
        # Service dependency injection
        services = _get_trigger_services()
        logger = services["logger"]

        # Parameter validation
        nglobal_parameters = get_params()
        if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
            logger.info("Trigger configuration request in OFFLINE mode")
            return success_response({"policies": [], "page": 0, "page_size": 0, "total": -1})

        # Pagination parameters with validation
        page = request.args.get("page", type=int, default=1)
        page_size = request.args.get("page_size", type=int, default=10)

        if page < 1:
            return error_response("Page number must be >= 1", 400)
        if page_size < 1 or page_size > 100:
            return error_response("Page size must be between 1 and 100", 400)

        # Service layer call with dependency injection
        params = {"enabled": True, "type": Type.PERIODICAL, "next_polling_min_time": True}
        query = filter_policies(params)

        # Database pagination
        result = db.paginate(query, page=page, per_page=page_size)
        policies = cast(list[TransferPolicy], result.items)

        response_data = {
            "policies": [p.to_dict() for p in policies],
            "page": result.page,
            "page_size": result.per_page,
            "total": result.total,
        }

        logger.info(f"Retrieved {len(policies)} trigger policies (page {page})")
        return success_response(response_data)

    except Exception as e:
        logger.error(f"Error in trigger configuration: {str(e)}")
        return error_response("Failed to get trigger configuration", 500)
