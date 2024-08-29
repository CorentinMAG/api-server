from flask import request, Blueprint
from dtr_common.types.requests import UpdateParamsJson
from api.services.parameters import update_params

bp = Blueprint("parameters", __name__)


@bp.route("/params", methods=["PUT"])
def update_parameters():
    """
    Update periodical parameters
    """
    payload: UpdateParamsJson = request.json
    payload = request.json
    param_id = payload["parameter_id"]
    next_polling_min_time = payload["next_polling_min_time"]
    update_params(param_id, next_polling_min_time)

    return "", 200
