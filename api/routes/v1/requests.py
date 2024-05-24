from flask import Blueprint, request
from typing import cast
from api.services.mode import get_mode
from api.services.requests import filter_requests, create_request, update_request
from common.constantes import Mode, State
from common.utils import parse_params
from common.types.filter import FilterRequestParams
from common.types.requests import CreateRequestJson, UpdateRequestJson
from sqlalchemy_pagination import paginate

bp = Blueprint("requests", __name__)


@bp.route("/requests", methods=["GET"])
def requests():
    """
    list all transfer requests
    output can be filtered by using query params
    - state: queued / completed / failed / in_progress
    - queues: name1,name2,...
    """

    nglobal_parameters = get_mode()
    mode = nglobal_parameters.mode

    if mode == Mode.OFFLINE:
        return {"requests": []}

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    parsed_params = cast(FilterRequestParams, parse_params(request.args.to_dict()))

    query = filter_requests(parsed_params)
    result = paginate(query, page=page, page_size=page_size)

    return {
        "requests": [r.to_dict(rules=("-policy.transfers",)) for r in result.items],
        "page": page,
        "page_size": page_size,
        "total": result.total,
    }, 200


@bp.route("/requests", methods=["POST"])
def new_requests():
    payload: CreateRequestJson = request.json

    files = payload["files"]
    policy_id = payload["policy"]

    create_request(policy_id, files)
    return "", 201


@bp.route("/requests", methods=["PUT"])
def update_requests():
    payload: UpdateRequestJson = request.json

    request_id = payload["request_id"]
    print(payload["status"])
    
    status = payload["status"]
    reason = payload.get("reason", None)

    update_request(request_id, status, reason)
    return "", 200
