from flask import Blueprint, request
from api.services.filters import get_params
from dtr_common.constantes import Mode
from api.services.policies import filter_policies
from api.db import db
from typing import cast
from api.models import TransferPolicy
from dtr_common.constantes import Type


bp = Blueprint("trigger", __name__)


@bp.route("/configuration/trigger", methods=["GET"])
def trigger():
    """
    return trigger configuration
    i.e all activated periodical transfer policies
    """

    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {"policies": [], "page": 0, "page_size": 0, "total": -1}
    else:
        page = request.args.get("page", type=int, default=1)
        page_size = request.args.get("page_size", type=int, default=10)
        params = {"enabled": True, "type": Type.PERIODICAL, "next_polling_min_time": True}
        query = filter_policies(params)
        result = db.paginate(query, page=page, per_page=page_size)
        policies = cast(list[TransferPolicy], result.items)
        return {
            "policies": [p.to_dict() for p in policies],
            "page": result.page,
            "page_size": result.per_page,
            "total": result.total,
        }, 200
