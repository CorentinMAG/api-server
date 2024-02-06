from flask import request, Blueprint
from .services.configuration import configure as set_configuration

bp = Blueprint("api", __name__)


@bp.route("/api", methods = ["PUT"])
def configure():
    payload = request.json
    is_configured = set_configuration(payload)

    if is_configured:
        return "", 201
    return "", 500