from __future__ import annotations
from flask import Blueprint, request
from api.utils.utils import custom_app 
from api.utils.utils import check_gparams_before_request

bp = Blueprint("trigger", __name__)

@bp.before_request
def handler():
    check_gparams_before_request()

@bp.route("/configuration/trigger", methods=["GET"])
def trigger():
    """
    Get trigger configuration and its associated transfer policies
    transfer policies list are paginated

    Args:
      None explicitly. Query parameters are taken from `request.args`:
        id (str, optional): trigger's identifier or default
        page (int): page number
        page_size (int): items per page
    Returns:
      flask.Response: A JSON response containing:
        configuration (dict): JSON representation of the trigger object
        pagination (dict): pagination parameters
        policies (list):  JSON representation of all transfer policies managed by the trigger
    """

    app = custom_app()

    # Pagination parameters with validation
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)
    id = request.args.get("id", type=str, default="default")

    trigger = app.services.triggers.get_by_name(id)
    paginated = app.services.triggers.get_policies(id, page, page_size)
    return {
        "configuration": trigger.to_dict(only=("name", "polling_interval")),
        "pagination": {
            "page": page,
            "per_page": page_size,
            "total": paginated.total,
            "pages": paginated.pages
        },
        "policies": [
            policy.to_dict(only=("id", "name", "src"))
            for policy in paginated.items
        ]
    }