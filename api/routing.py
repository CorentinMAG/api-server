from flask import request, Blueprint
from .services.configuration import configure as set_configuration

bp = Blueprint("api", __name__)


@bp.route("/api", methods = ["PUT"])
def configure():
    payload = request.json
    set_configuration(payload)
    return "", 201