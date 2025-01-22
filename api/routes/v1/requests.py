from flask import Blueprint, request
from typing import cast
from api.services.filters import get_params
from api.services.requests import (
    filter_requests,
    create_periodical_requests,
    update_request,
    create_commanded_request,
)
from api.models import TransferRequest
from dtr_common.utils import parse_params
from dtr_common.constantes import Mode
from dtr_common.schema import TriggerTransferRequestSchema, CommandedTransferRequestSchema

from api.db import db

bp = Blueprint("requests", __name__)


@bp.route("/requests", methods=["GET"])
def requests():
    """
    list all transfer requests
    output can be filtered by using query params
    - state: queued / successful / failed / in_progress
    - queues: name1,name2,...
    """

    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {
            "requests": [],
            "page": 0,
            "page_size": 0,
            "total": -1,
        }
    else:
        page = request.args.get("page", type=int, default=1)
        page_size = request.args.get("page_size", type=int, default=10)

        parsed_params = parse_params(request.args.to_dict())
        result = filter_requests(parsed_params)
        r = db.paginate(result, page=page, per_page=page_size)
        requests = cast(list[TransferRequest], r.items)
        return {
            "requests": [q.to_dict() for q in requests],
            "page": r.page,
            "page_size": r.per_page,
            "total": r.total,
        }, 200


@bp.route("/requests", methods=["POST"])
def new_requests():
    payload = request.json

    schema = TriggerTransferRequestSchema(**payload)

    create_periodical_requests(schema)
    return "", 200


@bp.route("/commanded/requests", methods=["POST"])
def new_commanded_request():
    payload = request.json
    schema = CommandedTransferRequestSchema(**payload)

    result = create_commanded_request(schema)
    if result:
        return {"message": result}, 200
    return {"error": "This policy doesn't exist"}, 404


@bp.route("/requests/<int:id>", methods=["PUT"])
def update_requests(id: int):
    payload = request.json

    nrequest = update_request(id, payload)
    if nrequest:
        return nrequest.to_dict(), 200
    return "", 200
