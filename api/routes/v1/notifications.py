from flask import Blueprint
from api.services.filters import get_params
from dtr_common.constantes import Mode, SubState
from api.services.requests import get_next_request

bp = Blueprint("notification", __name__)


@bp.route("/notifications", methods=["GET"])
def notification():
    ngparams = get_params()
    if ngparams is None or ngparams.mode == Mode.OFFLINE:
        return {"request": None}
    else:
        params = {"sub_state": SubState.NOTIFY}

        nrequest = get_next_request(params)
        if nrequest is not None:
            return {"request": nrequest.to_dict()}, 200
        return {"request": None}, 200
