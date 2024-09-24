from flask import request, Blueprint, current_app as app
from api.services.filters import get_params
from dtr_common.constantes import Mode
from api.services.requests import filter_requests
from sqlalchemy_pagination import paginate

bp = Blueprint("notification", __name__)


@bp.route("/notifications", methods=["GET"])
def notification():
    app.logger.debug("Get notifications")
    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {
            "requests": [],
            "page": 0,
            "page_size": 0,
            "total": -1,
        }
    else:
        page = request.args.get("page", type=int, default=1)
        page_size = request.args.get("page_size", type=int, default=10)

        params = {"sub_state": "notify"}

        query = filter_requests(params)
        result = paginate(query, page=page, page_size=page_size)

        return {
            "requests": [r.to_dict(rules=("-policy.transfers",)) for r in result.items],
            "page": page,
            "page_size": page_size,
            "total": result.total,
        }, 200
