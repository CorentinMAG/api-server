from __future__ import annotations

from typing import cast

from dtr_common.constantes import Mode, Type
from flask import Blueprint, current_app, request

from api.db import db
from api.models import TransferPolicy
from api.services.filters import get_params
from api.services.policies import filter_policies

bp = Blueprint("trigger", __name__)


@bp.route("/configuration/trigger", methods=["GET"])
def trigger():
    """
    Get trigger configuration - all activated periodical transfer policies.

    Query parameters:
    - page: int - Page number for pagination (default: 1)
    - page_size: int - Items per page (default: 10)
    """
    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        current_app.logger.info("Trigger configuration request in OFFLINE mode")
        return {"policies": [], "page": 0, "page_size": 0, "total": -1}

    # Pagination parameters with validation
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    # Service layer call with dependency injection
    params = {"enabled": True, "type": Type.PERIODICAL, "next_polling_min_time": True}
    query = filter_policies(params)

    # Database pagination
    result = db.paginate(query, page=page, per_page=page_size)
    policies = cast(list[TransferPolicy], result.items)

    return {
        "policies": [p.to_dict() for p in policies],
        "page": result.page,
        "page_size": result.per_page,
        "total": result.total,
    }
