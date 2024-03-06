from flask import request, Blueprint
from api.services.mode import get_mode
from common.constantes import Mode
from api.services.requests import filter_requests
from sqlalchemy_pagination import paginate

bp = Blueprint("notification", __name__)


@bp.route("/notifications", methods=["GET"])
def notification():
    nglobal_parameters = get_mode()
    mode = nglobal_parameters.mode

    if mode == Mode.OFFLINE.value:
        return {"requests": []}

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    params = {"state": "notify"}

    query = filter_requests(params)
    result = paginate(query, page=page, page_size=page_size)

    return {
        "requests": [r.to_dict(rules=("-policy.transfers",)) for r in result.items],
        "page": page,
        "page_size": page_size,
        "total": result.total,
    }, 200
