from flask import Blueprint
from api.services.filters import switch_mode, get_params
from dtr_common.constantes import Mode

bp = Blueprint("params", __name__)


@bp.route("/offline", methods=["POST"])
def set_offline_mode():
    """
    set DTR to offline mode
    """
    switch_mode(Mode.OFFLINE)
    return "", 200


@bp.route("/online", methods=["POST"])
def set_online_mode():
    """
    set DTR to online mode
    """

    switch_mode(Mode.ONLINE)
    return "", 200


@bp.route("/global_params", methods=["GET"])
def get_global_parameters():
    """
    return DTR global parameters
    """
    params = get_params()
    if params is None:
        return {
            "requests": [],
            "page": 0,
            "page_size": 0,
            "total": -1,
        }
    else:
        return params.to_dict(), 200
