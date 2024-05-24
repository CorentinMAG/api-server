from flask import request, Blueprint
from api.services.configuration import configure as set_configuration, unconfigure as del_configuration

bp = Blueprint("configuration", __name__)


@bp.route("/configure", methods=["POST"])
def configure():
    """
    delete the previous configuration and apply a new one
    """
    payload = request.json

    del_configuration(keep=["transfer_requests", "global_parameters"])
    set_configuration(payload)
    return "", 201


@bp.route("/configure", methods=["DELETE"])
def unconfigure():
    """
    delete all records from all tables in the database
    we can specify in the body if we want to delete all transfer requests
    """
    del_configuration(keep=["transfer_requests", "global_parameters"])
    return "", 200
