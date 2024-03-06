from flask import Blueprint
from api.services.mode import switch_mode, get_mode

bp = Blueprint("mode", __name__, url_prefix="/mode")


@bp.route("/offline", methods=["POST"])
def offline():
    """
    set DTR to offline mode
    """
    switch_mode("offline")
    return "", 200


@bp.route("/online", methods=["POST"])
def online():
    """
    set DTR to online mode
    """

    switch_mode("online")
    return "", 200


@bp.route("/status", methods=["GET"])
def status():
    """
    return DTR status
    """

    params = get_mode()
    return params.to_dict(), 200
