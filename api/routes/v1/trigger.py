from flask import Blueprint, request
from api.services.mode import get_mode
from common.constantes import Mode
from api.services.policies import filter_policies
from sqlalchemy_pagination import paginate


bp = Blueprint("trigger", __name__)


@bp.route("/configuration/trigger", methods=["GET"])
def trigger():
    """
    return trigger configuration
    i.e all activated periodical transfer policies
    """

    nglobal_parameters = get_mode()
    mode = nglobal_parameters.mode

    if mode == Mode.OFFLINE:
        return {"requests": []}

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)
    params = {"enabled": True, "type": "periodical"}
    query = filter_policies(params)
    result = paginate(query, page=page, page_size=page_size)
    return {
        "policies": [p.to_dict(rules=("-transfers.policy",)) for p in result.items],
        "page": page,
        "page_size": page_size,
        "total": result.total,
    }, 200

# add route to config worker