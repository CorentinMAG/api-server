from flask import request, Blueprint
from .services.configuration import configure as set_configuration

bp = Blueprint("api", __name__, url_prefix= "/api")


@bp.route("/configure", methods = ["POST"])
def configure():
    payload = request.json
    set_configuration(payload)
    return "", 201