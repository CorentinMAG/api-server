"""
Mode and global parameters API routes with dependency injection and error handling.
"""
from __future__ import annotations

from dtr_common.constantes import Mode
from flask import Blueprint
from api.utils.utils import custom_app

bp = Blueprint("mode", __name__)

@bp.route("/offline", methods=["POST"])
def set_offline_mode():
    """
    Set DTR to offline mode.
    """
    app = custom_app()
    app.services.params.switch_mode(Mode.OFFLINE)
    return "", 200



@bp.route("/online", methods=["POST"])
def set_online_mode():
    """
    Set DTR to online mode.
    """
    app = custom_app()
    app.services.params.switch_mode(Mode.ONLINE)
    return "", 200


@bp.route("/global_params", methods=["GET"])
def get_global_parameters():
    """
    Get DTR global parameters.
    """
    app = custom_app()
    gparams = app.services.params.get()
    return gparams.to_dict()

