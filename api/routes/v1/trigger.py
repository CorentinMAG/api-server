from __future__ import annotations
from dtr_common.constantes import Mode
from flask import Blueprint, current_app, request
from api.services.filters import get_params
from api.services.triggers import get_trigger, get_paginated_policies

bp = Blueprint("trigger", __name__)


@bp.route("/configuration/trigger", methods=["GET"])
def trigger():
    """
    Get trigger configuration as well as all active 
    transfer policies associated

    Query parameters:
    - name: str - trigger's identifier
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
    id = request.args.get("id", type=str, default="default")

    if id != "default":
        trigger = get_trigger(id)
    paginated = get_paginated_policies(id, page, page_size)
    policies = paginated.items
    return {
        "configuration": trigger.to_dict(only=("name", "polling_interval")) 
                         if id != "default" 
                         else {
                             "name": "default", 
                             "polling_interval": nglobal_parameters.polling_interval
                             },
        "pagination": {
            "page": page,
            "per_page": page_size,
            "total": paginated.total,
            "pages": paginated.pages
        },
        "policies": [
            policy.to_dict(only=("id", "name", "src")) 
            for policy in policies
        ]
    }
